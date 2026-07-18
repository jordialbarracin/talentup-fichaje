# TalentUP Fichaje — Firmware ESP32 + PN532 NFC

Firmware para ESP32 que lee tarjetas NFC con un módulo **PN532** vía SPI y envía el UID al backend **TalentUP Fichaje** para registrar entradas y salidas de empleados.

---

## 📦 Materiales necesarios

| Componente               | Cantidad | Coste aprox. (€) |
|--------------------------|----------|------------------|
| ESP32 (NodeMCU-32S / DOIT) | 1        | 6 – 10 €         |
| Módulo PN532 NFC (SPI)   | 1        | 8 – 12 €         |
| LED verde 5mm            | 1        | 0,10 €           |
| LED rojo 5mm             | 1        | 0,10 €           |
| Resistencia 220 Ω (LEDs) | 2        | 0,05 €           |
| Protoboard               | 1        | 1 – 3 €          |
| Cables Dupont (M-H)      | 10       | 1 – 2 €           |
| Fuente 5V / USB          | 1        | — (ya incluida con ESP32) |
| **Total aproximado**     |          | **16 – 27 €**     |

> Los precios son orientativos (AliExpress / Amazon / distribuidores locales).

---

## 🔌 Esquema de conexión (ESP32 → PN532)

### SPI — Conexión principal

| ESP32 GPIO | PN532 Pin | Cable color (ej.) |
|------------|-----------|-------------------|
| GPIO 5     | **NSS** (CS / SS) | 🟤 Marrón  |
| GPIO 18    | **SCK**           | 🟠 Naranja |
| GPIO 19    | **MISO**          | 🟡 Amarillo|
| GPIO 23    | **MOSI**          | 🟢 Verde   |
| 3.3V       | **VCC**           | 🔴 Rojo    |
| GND        | **GND**           | ⚫ Negro   |

### LEDs de estado

| ESP32 GPIO | Componente          | Conexión                     |
|------------|---------------------|------------------------------|
| GPIO 2     | LED verde (ánodo)   | → resistencia 220 Ω → GND   |
| GPIO 4     | LED rojo (ánodo)    | → resistencia 220 Ω → GND    |

> ⚠️ **Importante**: El PN532 funciona a **3.3V**. No conectar a 5V directamente. El ESP32 ya proporciona 3.3V por su pin de salida.

### Diagrama visual

```
ESP32                          PN532
┌─────────┐                  ┌─────────┐
│ GPIO 5  ├───── CS ────────→│ NSS     │
│ GPIO 18 ├───── SCK ───────→│ SCK     │
│ GPIO 19 │←──── MISO ───────│ MISO    │
│ GPIO 23 ├───── MOSI ──────→│ MOSI    │
│ 3.3V    ├─────────────────→│ VCC     │
│ GND     ├─────────────────→│ GND     │
│         │                  │         │
│ GPIO 2  ├──→ 220Ω ──→ LED verde ──→ GND
│ GPIO 4  ├──→ 220Ω ──→ LED rojo  ──→ GND
└─────────┘                  └─────────┘
```

---

## ⚙️ Configuración

Antes de compilar, edita las siguientes macros al inicio de `esp32_fichaje.ino`:

```cpp
#define WIFI_SSID     "TU_WIFI_SSID"        // Red WiFi
#define WIFI_PASS     "TU_WIFI_PASSWORD"    // Contraseña WiFi
#define BACKEND_URL   "http://192.168.1.100:8000"  // URL del backend
#define TENANT_ID     "default"             // ID del tenant/empresa
```

---

## 🛠️ Compilación y subida

### Opción A: Arduino IDE

1. Abre `esp32_fichaje.ino` en Arduino IDE.
2. **Instala las librerías necesarias** (Sketch → Include Library → Manage Libraries…):
   - `Adafruit PN532` (por Adafruit)
   - `ArduinoJson` (por Benoit Blanchon)
3. **Selecciona placa**: Tools → Board → ESP32 Dev Module (o tu modelo específico).
4. **Configura puerto**: Tools → Port → (el COM del ESP32).
5. **Ajusta parámetros** en las macros `#define` del sketch.
6. **Sube**: Sketch → Upload (Ctrl+U).

### Opción B: PlatformIO (recomendado)

Crea un `platformio.ini` en la raíz del proyecto:

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200

lib_deps =
    adafruit/Adafruit PN532 @ ^1.3.0
    bblanchon/ArduinoJson @ ^6.21.0
```

Luego:

```bash
pio run -t upload
pio device monitor
```

### Opción C: esptool.py (directo)

```bash
esptool.py --chip esp32 --port COM3 write_flash 0x1000 firmware.bin
```

---

## 📟 Monitor serie

La velocidad del monitor serie es **115200 baud**. Conecta y verás:

```
========================================
  TalentUP Fichaje - ESP32 NFC Reader
========================================
Conectando a WiFi: TU_WIFI_SSID
.....
WiFi conectado. IP: 192.168.1.42
PN532 detectado - Chip: 0x32 Rev: 1 V1.6

TalentUP Fichaje - Esperando tarjeta...
----------------------------------------
Tarjeta detectada - UID: A1B2C3D4
----------------------------------------
POST -> http://192.168.1.100:8000/api/clock/nfc
Body: {"nfc_uid":"A1B2C3D4","tenant_id":"default"}
HTTP 200: {"status":"ok","employee":"Carlos","type":"Entrada","message":"14:32"}
OK: Carlos - Entrada 14:32
```

---

## 🔧 Funcionamiento

1. El ESP32 se conecta al WiFi configurado.
2. Inicializa el PN532 en modo SAM (lectura pasiva de tarjetas ISO 14443A).
3. Espera tarjetas NFC (MIFARE Classic, NTAG, etc.).
4. Al detectar una tarjeta:
   - Lee su **UID** (identificador único de 4 o 7 bytes).
   - Envía un **POST** JSON al backend: `{ "nfc_uid": "A1B2C3D4", "tenant_id": "default" }`.
   - Muestra la respuesta del backend por Serial.
   - Enciende LED **verde** si OK, **rojo** si error.
5. Espera **2 segundos** antes de leer otra tarjeta (debounce).
6. Si el WiFi se pierde, reintenta cada 5 segundos.
7. Si el backend no responde, muestra error y LED rojo.

---

## 🐛 Posibles problemas

| Síntoma                     | Causa probable                          | Solución                                |
|-----------------------------|-----------------------------------------|-----------------------------------------|
| "No se detecta PN532"       | Conexiones SPI incorrectas              | Revisar cableado, verificar 3.3V        |
| No conecta WiFi             | SSID/pass incorrectos                   | Revisar macros de configuración         |
| "No se pudo contactar backend" | Backend caído o IP incorrecta         | Verificar BACKEND_URL y que el backend corra |
| Lecturas duplicadas         | Tarjeta demasiado tiempo sobre el lector | Aumentar DEBOUNCE_MS                    |
| LED no enciende             | Polaridad invertida o resistencia faltante | Revisar conexión ánodo → GPIO → resistencia → GND |

---

## 📁 Estructura de archivos

```
hardware/esp32_fichaje/
├── esp32_fichaje.ino      # Firmware principal
├── README.md              # Este archivo
└── platformio.ini         # (opcional) Config PlatformIO
```

---

## 📄 Licencia

MIT — Proyecto TalentUP Fichaje.
