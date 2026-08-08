#!/usr/bin/env python3
"""
TalentUP Fichaje — Simulador del flujo completo de un fichaje NFC (ESP32 → backend).

Simula lo que hace el firmware del ESP32-CYD + PN532:

  1. Genera un tag NFC con UID aleatorio (formato hex, como lo lee el PN532).
  2. Envía POST {nfc_uid, tenant_id} al endpoint /api/clock/nfc del backend.
  3. Verifica la respuesta HTTP y el campo `ok` del JSON.
  4. Si el backend NO responde (timeout / conexión rechazada), encola el fichaje
     en una cola offline (archivo JSON) — igual que el firmware lo guarda en SPIFFS.
  5. Si el backend responde OK, primero reintentá los fichajes pendientes de la
     cola offline (drain) y luego registra el nuevo.
  6. Loggea cada acción con timestamp ISO-8601.

Uso:
    python simulate_nfc_flow.py
    python simulate_nfc_flow.py --backend-url http://localhost:8000 --tenant-id default
    python simulate_nfc_flow.py --uid NFC001            # UID fijo (tarjeta conocida)
    python simulate_nfc_flow.py --count 5                # 5 fichajes seguidos
    python simulate_nfc_flow.py --offline-file /tmp/offline_queue.json

Requisitos:
    - Backend corriendo en --backend-url (default http://localhost:8000)
    - `requests` instalado (pip install requests)
    - Para que el fichaje sea aceptado, el UID debe existir en la BD
      (seed: NFC001, NFC002). Con --uid random se simula una tarjeta no
      registrada → el backend responde 404 y el script lo encola offline.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover
    print("ERROR: falta 'requests'. Instala con: pip install requests", file=sys.stderr)
    sys.exit(2)

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

def _ts() -> str:
    """Timestamp ISO-8601 con zona horaria (UTC)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(msg: str, *, level: str = "INFO") -> None:
    """Loggea una línea con timestamp. level ∈ INFO, OK, WARN, ERROR, DEBUG."""
    print(f"[{_ts()}] [{level:5}] {msg}", flush=True)


# ─────────────────────────────────────────────────────────────────────────────
# Cola offline (archivo JSON) — análoga al SPIFFS del ESP32
# ─────────────────────────────────────────────────────────────────────────────

def load_queue(path: str) -> list[dict]:
    """Carga la cola offline desde disco. Devuelve [] si no existe o está corrupta."""
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        log(f"Cola offline con formato inesperado (no es lista): {path}", level="WARN")
        return []
    except (json.JSONDecodeError, OSError) as e:
        log(f"No se pudo leer cola offline ({e}); arrancando vacía", level="WARN")
        return []


def save_queue(path: str, queue: list[dict]) -> None:
    """Persiste la cola offline a disco de forma atómica."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
    tmp.replace(p)  # rename atómico


# ─────────────────────────────────────────────────────────────────────────────
# Tag NFC
# ─────────────────────────────────────────────────────────────────────────────

def random_nfc_uid() -> str:
    """
    Genera un UID NFC aleatorio de 4 bytes en hex uppercase (formato PN532).
    Ej: 'A1B2C3D4'. El backend normaliza y acepta también formato con comas ':'.
    """
    return "".join(f"{random.randint(0, 255):02X}" for _ in range(4))


def make_record(uid: str, tenant_id: str) -> dict:
    """Construye el registro de fichaje que se envía al backend (y se encola offline)."""
    return {
        "nfc_uid": uid,
        "tenant_id": tenant_id,
        "timestamp": _ts(),          # momento de la lectura física del tag
        "source": "simulate_nfc_flow",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Comunicación con el backend
# ─────────────────────────────────────────────────────────────────────────────

def send_to_backend(record: dict, backend_url: str, *, timeout: float = 10.0) -> dict | None:
    """
    Envía un POST a /api/clock/nfc.

    Devuelve el JSON de respuesta si el backend respondió 2xx.
    Devuelve None si el backend no respondió (timeout / conexión rechazada)
    o si respondió con error HTTP (4xx/5xx) — en ambos casos el fichaje se
    considera NO confirmado y debe encolarse offline.
    """
    url = backend_url.rstrip("/") + "/api/clock/nfc"
    payload = {"nfc_uid": record["nfc_uid"], "tenant_id": record["tenant_id"]}
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
    except requests.exceptions.ConnectionError as e:
        log(f"Backend inalcanzable (ConnectionError): {e}", level="ERROR")
        return None
    except requests.exceptions.Timeout:
        log(f"Backend no respondió en {timeout}s (timeout)", level="ERROR")
        return None
    except requests.exceptions.RequestException as e:
        log(f"Error de red inesperado: {e}", level="ERROR")
        return None

    # El backend responde 201 en éxito (status_code=201 en el router)
    if 200 <= resp.status_code < 300:
        try:
            data = resp.json()
        except ValueError:
            log(f"Respuesta 2xx pero sin JSON válido: {resp.text[:200]}", level="WARN")
            return None
        return data

    # Error HTTP controlado (404 tarjeta no registrada, 400, 429 rate limit, 5xx…)
    log(f"Backend respondió HTTP {resp.status_code}: {resp.text[:200]}", level="WARN")
    # 404 = tarjeta no registrada → no es un fallo de backend, pero el fichaje
    # no se registró. Lo encolamos igual para no perderlo (igual que el ESP32).
    return None


def drain_queue(path: str, backend_url: str, *, timeout: float = 10.0) -> int:
    """
    Vacia la cola offline reintentando cada fichaje pendiente contra el backend.
    Devuelve el número de fichajes que se pudieron enviar con éxito.
    Si el backend vuelve a fallar a mitad del drain, los no enviados permanecen en cola.
    """
    queue = load_queue(path)
    if not queue:
        return 0

    log(f"Drain cola offline: {len(queue)} fichaje(s) pendiente(s)")
    remaining: list[dict] = []
    sent = 0

    for rec in queue:
        log(f"  Reintentando UID={rec.get('nfc_uid')} (original: {rec.get('timestamp')})")
        data = send_to_backend(rec, backend_url, timeout=timeout)
        if data is None:
            # Backend sigue caído: lo dejamos en cola y salimos (no tiene sentido
            # seguir probando si el backend está abajo).
            remaining.append(rec)
            log("Backend sigue sin responder; conservando fichajes restantes en cola", level="WARN")
            remaining.extend(queue[queue.index(rec) + 1:])
            break
        sent += 1
        log(f"  OK → {data.get('employee_name', '?')} / {data.get('type', '?')} "
            f"({data.get('message', '')})", level="OK")

    save_queue(path, remaining)
    log(f"Drain completado: {sent} enviados, {len(remaining)} siguen en cola", level="OK")
    return sent


# ─────────────────────────────────────────────────────────────────────────────
# Flujo principal (un fichaje)
# ─────────────────────────────────────────────────────────────────────────────

def simulate_one(
    *,
    backend_url: str,
    tenant_id: str,
    uid: str | None,
    offline_file: str,
    timeout: float,
) -> dict:
    """
    Ejecuta el flujo completo de un fichaje NFC y devuelve un dict con el resultado.

    Lógica (igual que el firmware del ESP32):
      - Genera (o usa) el UID del tag.
      - Intenta enviar al backend.
      - Si el backend responde OK → drena la cola offline primero, luego cuenta
        este fichaje como registrado en vivo.
      - Si el backend NO responde → encola el fichaje en la cola offline.
    """
    tag_uid = uid if uid else random_nfc_uid()
    log(f"Tag NFC detectado: UID={tag_uid} (tenant={tenant_id})")

    record = make_record(tag_uid, tenant_id)

    data = send_to_backend(record, backend_url, timeout=timeout)

    if data is not None:
        # Backend OK: primero vaciamos la cola offline (si hay pendientes),
        # luego reportamos el fichaje en vivo.
        queue = load_queue(offline_file)
        if queue:
            log(f"Backend online con {len(queue)} fichaje(s) offline pendiente(s) — drenando", level="INFO")
            drain_queue(offline_file, backend_url, timeout=timeout)

        log(f"Fichaje registrado en vivo → {data.get('employee_name', '?')} | "
            f"tipo={data.get('type', '?')} | hora={data.get('time', '?')}", level="OK")
        return {"status": "online", "uid": tag_uid, "response": data}

    # Backend caído: encolar offline
    queue = load_queue(offline_file)
    queue.append(record)
    save_queue(offline_file, queue)
    log(f"Backend no disponible → fichaje encolado offline "
        f"(cola={len(queue)} item(s) en {offline_file})", level="WARN")
    return {"status": "offline_queued", "uid": tag_uid, "queue_len": len(queue)}


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Simula el flujo completo de un fichaje NFC (ESP32 → backend) "
                    "con cola offline análoga al SPIFFS del firmware.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--backend-url",
        default=os.environ.get("BACKEND_URL", "http://localhost:8000"),
        help="URL base del backend (default: http://localhost:8000)",
    )
    p.add_argument(
        "--tenant-id",
        default=os.environ.get("TENANT_ID", "default"),
        help="Tenant ID (default: 'default')",
    )
    p.add_argument(
        "--uid",
        default=None,
        help="UID fijo a usar en vez de uno aleatorio (ej: NFC001 para tarjeta seed). "
             "Si se omite, se genera un UID hex aleatorio de 4 bytes.",
    )
    p.add_argument(
        "--count",
        type=int,
        default=1,
        help="Número de fichajes a simular seguidos (default: 1)",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Segundos entre fichajes cuando --count > 1 (default: 1.0)",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout HTTP en segundos (default: 10)",
    )
    p.add_argument(
        "--offline-file",
        default=os.environ.get("NFC_OFFLINE_FILE", "nfc_offline_queue.json"),
        help="Ruta del archivo JSON de cola offline (default: nfc_offline_queue.json)",
    )
    p.add_argument(
        "--drain-only",
        action="store_true",
        help="No simular fichaje nuevo; solo drenar la cola offline existente.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    log("=" * 60)
    log("TalentUP Fichaje — Simulador flujo NFC (ESP32 → backend)")
    log("=" * 60)
    log(f"Backend:    {args.backend_url}")
    log(f"Tenant:     {args.tenant_id}")
    log(f"Cola offl.:  {os.path.abspath(args.offline_file)}")
    log(f"UID:        {args.uid or '<aleatorio>'}")
    log(f"Count:      {args.count}  intervalo={args.interval}s  timeout={args.timeout}s")

    # Estado inicial de la cola
    initial_queue = load_queue(args.offline_file)
    if initial_queue:
        log(f"Cola offline inicial: {len(initial_queue)} fichaje(s) pendiente(s)", level="WARN")

    # Modo drain-only
    if args.drain_only:
        sent = drain_queue(args.offline_file, args.backend_url, timeout=args.timeout)
        log(f"Drain-only finalizado: {sent} fichaje(s) enviados", level="OK")
        return 0

    # Simulación de N fichajes
    results = []
    for i in range(args.count):
        if i > 0 and args.interval > 0:
            time.sleep(args.interval)
        log("-" * 60)
        log(f"Fichaje {i + 1}/{args.count}")
        res = simulate_one(
            backend_url=args.backend_url,
            tenant_id=args.tenant_id,
            uid=args.uid,
            offline_file=args.offline_file,
            timeout=args.timeout,
        )
        results.append(res)

    # Resumen final
    online = sum(1 for r in results if r["status"] == "online")
    queued = sum(1 for r in results if r["status"] == "offline_queued")
    final_queue = load_queue(args.offline_file)

    log("=" * 60)
    log(f"Resumen: {online} online, {queued} encolados offline, "
        f"{len(final_queue)} pendientes en cola final")
    log("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())