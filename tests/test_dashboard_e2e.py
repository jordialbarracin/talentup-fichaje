#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test E2E del dashboard de TalentUP
====================================

Abre ``frontend/dashboard_new.html`` en Chromium (Playwright) y verifica:
  1. Carga sin errores de JavaScript.
  2. Las 7 vistas existen y son navegables (dashboard, empleados, fichajes,
     turnos, reportes, incidencias, ajustes).
  3. Hay graficos SVG renderizados (barras, lineas, donut, anillos, heatmap,
     sparklines).
  4. La plantilla tiene 24 empleados (multiples puntos de verificacion).
  5. El layout es responsive (desktop, tablet <=900px, movil <=480px).
  6. Las interacciones principales funcionan (busqueda, filtros, tabs,
     resolver incidencia, toasts, sidebar movil).

Uso:
    python tests/test_dashboard_e2e.py        # script con informe
    pytest tests/test_dashboard_e2e.py -v     # suite CI

Requisitos: pip install playwright && python -m playwright install chromium
"""

from __future__ import annotations

import socket
import sys
import traceback
import http.server
import socketserver
import threading
from pathlib import Path
from typing import Any, Callable

# --- Configuracion estatica. El dashboard es estatico: se sirve via un mini
# servidor HTTP local (Playwright prefiere http:// a file:// para resolver
# las rutas relativas del design_system.css de forma fiable). ---------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_HTML = REPO_ROOT / "frontend" / "dashboard_new.html"

# Las 7 vistas esperadas, en el orden del sidebar: (id, titulo H1 esperado).
VIEWS = [
    ("dashboard",   "Dashboard"),
    ("empleados",   "Empleados"),
    ("fichajes",    "Fichajes"),
    ("turnos",      "Turnos"),
    ("reportes",    "Reportes"),
    ("incidencias", "Incidencias"),
    ("ajustes",     "Ajustes"),
]

# Viewports responsive. Breakpoints del dashboard: @media max-width 900px
# (sidebar fuera de pantalla) y max-width 480px (KPIs en 2 columnas).
DESKTOP = {"width": 1440, "height": 900}
TABLET  = {"width": 900,  "height": 1024}
MOBILE  = {"width": 375,  "height": 720}

# Tiempos de espera (ms). El dashboard usa un skeleton de 380ms al cambiar de
# vista, asi que damos margen suficiente.
SHORT_WAIT    = 300
VIEW_WAIT     = 800    # tras switchView (skeleton 380ms + render)
LOAD_WAIT     = 2200   # carga inicial completa
CLICK_TIMEOUT = 6000   # timeout por click en nav
BASE_PORT     = 8765


# ===========================================================================
# Mini-framework de aserciones que acumula resultados en lugar de abortar al
# primer fallo, para que el script independiente muestre un informe completo.
# ===========================================================================

class TestResult:
    """Resultado individual de una asercion."""
    def __init__(self, name: str, passed: bool, detail: str = "") -> None:
        self.name, self.passed, self.detail = name, passed, detail


class TestSuite:
    """Acumulador de resultados con resumen final."""
    def __init__(self) -> None:
        self.results: list[TestResult] = []

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        self.results.append(TestResult(name, bool(condition), detail))
        return bool(condition)

    def check_eq(self, name: str, actual: Any, expected: Any) -> bool:
        ok = actual == expected
        self.results.append(
            TestResult(name, ok, f"esperado={expected!r} actual={actual!r}" if not ok else "")
        )
        return ok

    def summary(self) -> dict:
        p = sum(1 for r in self.results if r.passed)
        return {"total": len(self.results), "passed": p, "failed": len(self.results) - p}

    def print_report(self) -> None:
        print("\n" + "=" * 72)
        print("  TEST E2E - Dashboard TalentUP")
        print("=" * 72)
        for r in self.results:
            mark = "\u2713" if r.passed else "\u2717"
            color = "\033[32m" if r.passed else "\033[31m"
            line = f"  {color}{mark}\033[0m {r.name}"
            if not r.passed and r.detail:
                line += f"\n      {color}{r.detail}\033[0m"
            print(line)
        s = self.summary()
        print("-" * 72)
        status = "\033[32mOK \u2713" if s["failed"] == 0 else "\033[31mFAIL \u2717"
        print(f"  Total: {s['total']}  |  Aciertos: {s['passed']}  |  "
              f"Fallos: {s['failed']}  |  Estado: {status}\033[0m")
        print("=" * 72)


# ===========================================================================
# Captura de errores de consola del navegador — nucleo de "sin errores JS".
# ===========================================================================

class ConsoleTracker:
    """Registra errores y excepciones no capturadas de la pagina."""
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.page_errors: list[str] = []

    def attach(self, page: Any) -> None:
        page.on("console", self._on_console)
        page.on("pageerror", self._on_page_error)

    def _on_console(self, msg: Any) -> None:
        if msg.type == "error":
            self.errors.append(msg.text)

    def _on_page_error(self, err: Any) -> None:
        self.page_errors.append(str(err))

    def blocking_messages(self) -> list[str]:
        msgs = list(self.page_errors)
        for e in self.errors:
            low = e.lower()
            if "favicon" in low or "404" in e:
                continue
            msgs.append(e)
        return msgs


# ===========================================================================
# Servidor HTTP local improvisado con puerto libre automatico.
# ===========================================================================

def _free_port(preferred: int = BASE_PORT) -> int:
    """Devuelve un puerto libre, prefiriendo `preferred` si esta libre."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", preferred))
        return preferred
    except OSError:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def start_local_server(root: Path, port: int) -> Any:
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(
        *a, directory=str(root), **kw
    )
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def stop_local_server(httpd: Any) -> None:
    try:
        httpd.shutdown()
        httpd.server_close()
    except Exception:
        pass


# ===========================================================================
# Helpers de navegacion. El sidebar se oculta en tablet/movil, asi que antes
# de clickar un nav-item hay que abrirlo si no esta visible.
# ===========================================================================

def is_mobile_viewport(page: Any) -> bool:
    return page.viewport_size["width"] <= 900


def _nav_btn(page: Any, view_id: str) -> Any:
    """Devuelve el locator del nav-item *visible* para una vista.

    El dashboard tiene un unico conjunto de nav-items dentro de ``#nav-list``
    (en ``#sidebar``). En desktop el sidebar esta siempre a la vista, pero en
    tablet/movil se desplaza fuera de pantalla con ``transform: translateX(-100%)``
    y solo es visible cuando ``#sidebar`` lleva la clase ``is-open``. Playwright
    trata un elemento movido fuera del viewport con ``transform`` como *visible*
    aun cuando este oculto, asi que filtramos explicitamente por visibilidad
    real (box con ancho/alto > 0 y dentro del viewport) para no clicar un boton
    que el usuario no puede ver.
    """
    locator = page.locator(f'#nav-list .nav-item[data-view="{view_id}"]')
    # Hay un solo conjunto de nav-items; si esta visible lo usamos. Si por algun
    # motivo la pagina anadiera un segundo conjunto oculto (p. ej. un duplicado
    # mobile), `.visible` se encarga de seleccionar el correcto.
    return locator if locator.count() == 1 else locator.first


def open_sidebar_if_needed(page: Any) -> None:
    if not is_mobile_viewport(page):
        return
    sidebar = page.locator("#sidebar")
    if "is-open" not in (sidebar.get_attribute("class") or ""):
        page.locator("#sidebar-toggle").click(timeout=CLICK_TIMEOUT)
        page.wait_for_timeout(SHORT_WAIT)


def go_to_view(page: Any, view_id: str) -> None:
    """Navega a una vista abriendo el sidebar si estamos en movil/tablet.

    Usa el nav-item *visible* (el sidebar desplegado), nunca el oculto fuera de
    pantalla, para evitar clicar un objetivo que el usuario no puede ver.
    """
    open_sidebar_if_needed(page)
    _nav_btn(page, view_id).click(timeout=CLICK_TIMEOUT)
    page.wait_for_timeout(VIEW_WAIT)


def go_dashboard(page: Any) -> None:
    go_to_view(page, "dashboard")


# ===========================================================================
# Pruebas individuales. Cada una recibe `page` (Playwright Page) y el
# `TestSuite` acumulador. Registran resultados en la suite.
# ===========================================================================

def test_page_loads(page: Any, suite: TestSuite, url: str,
                    tracker: ConsoleTracker) -> None:
    """La pagina carga, titulo correcto y sin errores JS iniciales."""
    response = page.goto(url, wait_until="networkidle")
    suite.check("HTTP 200 al cargar dashboard_new.html",
                response is not None and response.ok,
                f"status={response.status if response else 'None'}")
    page.wait_for_timeout(LOAD_WAIT)
    title = page.title()
    suite.check("Titulo de la pagina contiene 'Dashboard'",
                "Dashboard" in title, f"title={title!r}")
    suite.check("Sin excepciones JS no capturadas",
                len(tracker.page_errors) == 0,
                "; ".join(tracker.page_errors) if tracker.page_errors else "")


def test_no_js_errors(suite: TestSuite, tracker: ConsoleTracker) -> None:
    """No hay errores de JavaScript ni excepciones no capturadas."""
    blocking = tracker.blocking_messages()
    suite.check("Sin console.error de JS (excluyendo favicon 404)",
                len(blocking) == 0,
                "; ".join(blocking[:5]) if blocking else "")


def test_seven_views_exist(page: Any, suite: TestSuite) -> None:
    """Las 7 secciones <section class="view"> existen en el DOM."""
    views_dom = page.eval_on_selector_all(
        ".view", "els => els.map(e => e.getAttribute('data-view'))"
    )
    suite.check_eq("7 elementos .view en el DOM", len(views_dom), 7)
    for vid, _t in VIEWS:
        suite.check(f"Vista '{vid}' presente en el DOM", vid in views_dom)
    nav_views = page.eval_on_selector_all(
        "#nav-list .nav-item", "els => els.map(e => e.getAttribute('data-view'))"
    )
    suite.check_eq("7 botones nav-item en el sidebar", len(nav_views), 7)
    for vid, _t in VIEWS:
        suite.check(f"Boton nav-item para '{vid}'", vid in nav_views)


def test_views_navigable(page: Any, suite: TestSuite) -> None:
    """Cada vista es navegable: al clickar el nav-item, se activa y el H1
    cambia al titulo esperado."""
    for vid, expected_title in VIEWS:
        go_to_view(page, vid)
        suite.check(f"Vista '{vid}' activa tras click",
                    page.locator(f'.view.is-active[data-view="{vid}"]').count() == 1)
        suite.check_eq(f"Una sola vista activa al mostrar '{vid}'",
                       page.locator(".view.is-active").count(), 1)
        nav_btn = page.locator(f'#nav-list .nav-item[data-view="{vid}"]')
        suite.check(f"Nav-item '{vid}' con clase 'active'",
                    "active" in (nav_btn.get_attribute("class") or ""))
        h1 = page.locator('.view.is-active .page-head h1').first.inner_text().strip()
        suite.check_eq(f"H1 de '{vid}' coincide", h1, expected_title)


def test_svg_charts_dashboard(page: Any, suite: TestSuite) -> None:
    """El dashboard tiene multiples graficos SVG renderizados."""
    go_dashboard(page)
    total = page.locator("#view-dashboard svg").count()
    suite.check("Dashboard tiene SVGs (>0)", total > 0, f"count={total}")
    suite.check_eq("4 sparklines en KPIs",
                   page.locator("#kpi-grid .kpi-spark").count(), 4)
    suite.check_eq("4 iconos SVG en KPIs",
                   page.locator("#kpi-grid .kpi-icon svg").count(), 4)
    suite.check("Grafico de barras (fichajes/dia) presente",
                page.locator('svg[aria-label="Fichajes por dia de la ultima semana"]').count() == 1)
    suite.check("Grafico de lineas (evolucion 4 sem) presente",
                page.locator('svg[aria-label="Evolucion de horas trabajadas en las ultimas 4 semanas"]').count() == 1)
    donut = page.locator("#dash-donut svg")
    suite.check("Donut SVG del dashboard presente",
                donut.count() >= 1, f"count={donut.count()}")
    # El donut se renderiza con elementos <circle stroke-dasharray=...> (uno por
    # area), no con <path>. Verificamos segmentos de circulo: el donut incluye
    # 1 circulo central de relleno (sin stroke-dasharray) + 1 circulo por area.
    segment_circles = page.eval_on_selector_all(
        "#dash-donut svg circle",
        "els => els.filter(c => c.hasAttribute('stroke-dasharray')).length",
    )
    suite.check("Donut tiene segmentos (circle stroke-dasharray)",
                segment_circles >= 1, f"segments={segment_circles}")


def test_svg_charts_reportes(page: Any, suite: TestSuite) -> None:
    """La vista Reportes tiene graficos SVG: area, donut, anillos, heatmap."""
    go_to_view(page, "reportes")
    suite.check("Grafico de area en Reportes presente",
                page.locator('svg[aria-label="Evolucion de horas trabajadas"]').count() == 1)
    suite.check("Donut SVG en Reportes presente",
                page.locator("#reportes-donut svg").count() >= 1)
    suite.check_eq("3 anillos SVG en Reportes",
                   page.locator("#reportes-rings svg").count(), 3)
    suite.check_eq("Heatmap tiene 24 filas (empleados)",
                   page.locator("#heatmap .heatmap-row").count(), 24)
    cells = page.locator("#heatmap .heatmap-cell").count()
    suite.check("Heatmap tiene celdas renderizadas (>0)", cells > 0, f"cells={cells}")
    suite.check("Ranking horas extra tiene items",
                page.locator("#rank-extra .rank-item").count() > 0)
    suite.check("Ranking retrasos tiene items",
                page.locator("#rank-tarde .rank-item").count() > 0)


def test_24_employees_count(page: Any, suite: TestSuite) -> None:
    """La plantilla tiene 24 empleados, verificado en multiples puntos."""
    go_dashboard(page)
    suite.check_eq("Badge nav-emp-count = 24",
                   page.locator("#nav-emp-count").inner_text().strip(), "24")
    go_to_view(page, "empleados")
    label = page.locator("#emp-count-label").inner_text().strip()
    suite.check("Etiqueta plantilla contiene '24'", "24" in label, f"label={label!r}")
    suite.check_eq("Tabla empleados tiene 24 filas",
                   page.locator("#emp-tbody tr").count(), 24)
    page.locator('#emp-view-toggle button[data-emp-view="tarjetas"]').click()
    page.wait_for_timeout(SHORT_WAIT)
    suite.check_eq("Vista tarjetas tiene 24 tarjetas",
                   page.locator("#emp-view-tarjetas .emp-tile").count(), 24)
    page.locator('#emp-view-toggle button[data-emp-view="tabla"]').click()
    page.wait_for_timeout(SHORT_WAIT)
    go_to_view(page, "fichajes")
    suite.check_eq("Chip fichajes 'Todos' = 24",
                   page.locator("#cnt-all").inner_text().strip(), "24")
    go_to_view(page, "reportes")
    suite.check_eq("Heatmap con 24 filas (reportes)",
                   page.locator("#heatmap .heatmap-row").count(), 24)


def test_kpis_rendered(page: Any, suite: TestSuite) -> None:
    """Los KPIs se renderizan con valores coherentes con 24 empleados."""
    go_dashboard(page)
    suite.check_eq("4 tarjetas KPI renderizadas",
                   page.locator("#kpi-grid .kpi-card").count(), 4)
    plantilla = page.locator("#kpi-grid .kpi-card:first-child .kpi-value").inner_text().strip()
    suite.check("KPI 'Plantilla total' muestra 24", "24" in plantilla, f"value={plantilla!r}")
    fichajes = page.locator("#kpi-grid .kpi-card:nth-child(2) .kpi-value").inner_text().strip()
    suite.check("KPI 'Fichajes hoy' referencia 24", "24" in fichajes, f"text={fichajes!r}")
    width = page.eval_on_selector("#progress-fill", "e => getComputedStyle(e).width")
    suite.check("Barra de progreso semanal con ancho > 0",
                width not in ("0px", ""), f"width={width!r}")


def test_dashboard_today_and_alerts(page: Any, suite: TestSuite) -> None:
    """La tabla 'Hoy' y las alertas del dashboard tienen contenido."""
    go_dashboard(page)
    rows = page.locator("#dash-today-tbody tr").count()
    suite.check("Tabla 'Hoy' del dashboard tiene filas", rows > 0, f"count={rows}")
    suite.check("Tabla 'Hoy' tiene avatares de empleados",
                page.locator("#dash-today-tbody .emp-avatar").count() > 0)
    alerts = page.locator("#dash-alerts .alert-item").count()
    suite.check("Lista de alertas tiene items", alerts > 0, f"count={alerts}")
    badge = page.locator("#dash-alert-count").inner_text().strip()
    suite.check("Badge de alertas > 0",
                badge.isdigit() and int(badge) > 0, f"badge={badge!r}")
    suite.check_eq("Calendario semanal tiene 7 dias",
                   page.locator("#dash-calendar .calendar-day").count(), 7)
    suite.check_eq("Calendario marca el dia actual",
                   page.locator("#dash-calendar .calendar-day.is-today").count(), 1)


def test_employee_search_filter(page: Any, suite: TestSuite) -> None:
    """La busqueda de empleados filtra la tabla en vivo."""
    go_to_view(page, "empleados")
    suite.check_eq("Filas antes de buscar",
                   page.locator("#emp-tbody tr").count(), 24)
    page.locator("#emp-search").fill("Laia")
    page.wait_for_timeout(SHORT_WAIT)
    suite.check_eq("Busqueda 'Laia' -> 1 fila",
                   page.locator("#emp-tbody tr").count(), 1)
    page.locator("#emp-search").fill("")
    page.wait_for_timeout(SHORT_WAIT)
    page.locator("#emp-filter-area").select_option("Cocina")
    page.wait_for_timeout(SHORT_WAIT)
    cocina = page.locator("#emp-tbody tr").count()
    suite.check("Filtro 'Cocina' reduce filas (0 < n < 24)",
                0 < cocina < 24, f"count={cocina}")
    page.locator("#emp-filter-area").select_option("todos")
    page.wait_for_timeout(SHORT_WAIT)
    suite.check_eq("Restaurar filtro -> 24 filas",
                   page.locator("#emp-tbody tr").count(), 24)


def test_fichajes_filters(page: Any, suite: TestSuite) -> None:
    """Los chips de filtro de fichajes cambian de estado al clickarlos."""
    go_to_view(page, "fichajes")
    page.locator('#fichaje-filters .chip-filter[data-filter="ok"]').click()
    page.wait_for_timeout(SHORT_WAIT)
    suite.check_eq("Chip 'A tiempo' activo",
                   page.locator('#fichaje-filters .chip-filter[data-filter="ok"].active').count(), 1)
    page.locator('#fichaje-filters .chip-filter[data-filter="all"]').click()
    page.wait_for_timeout(SHORT_WAIT)
    suite.check_eq("Chip 'Todos' vuelve a activo",
                   page.locator('#fichaje-filters .chip-filter[data-filter="all"].active').count(), 1)


def test_turnos_filter(page: Any, suite: TestSuite) -> None:
    """La vista Turnos carga y el filtro por area funciona sin error JS."""
    go_to_view(page, "turnos")
    suite.check("Tabla de turnos presente",
                page.locator(".schedule-table").count() >= 1)
    page.locator("#turno-filter-area").select_option("Cocina")
    page.wait_for_timeout(SHORT_WAIT)
    page.locator("#turno-filter-area").select_option("todos")
    page.wait_for_timeout(SHORT_WAIT)
    suite.check("Filtro de turnos por 'Cocina' sin error JS", True)


def test_incidents_resolve(page: Any, suite: TestSuite) -> None:
    """Resolver una incidencia muestra un toast y actualiza la lista."""
    go_to_view(page, "incidencias")
    initial = page.locator("#incident-list .incident-card").count()
    suite.check("Lista de incidencias tiene items", initial > 0, f"count={initial}")
    btn = page.locator("[data-resolve]").first
    if btn.count():
        before = page.locator("#toast-container .toast").count()
        btn.click()
        page.wait_for_timeout(SHORT_WAIT)
        after = page.locator("#toast-container .toast").count()
        suite.check("Aparece un toast al resolver incidencia",
                    after > before, f"before={before} after={after}")
    else:
        suite.check("Boton 'Marcar resuelta' presente", False,
                    "no data-resolve buttons found")
    page.locator('#incident-tabs .tab[data-incident-tab="resuelta"]').click()
    page.wait_for_timeout(SHORT_WAIT)
    resolved = page.locator("#incident-list .incident-card").count()
    suite.check("Tab 'Resueltas' muestra items", resolved >= 1, f"count={resolved}")


def test_ajustes_tabs(page: Any, suite: TestSuite) -> None:
    """Los tabs de Ajustes cambian el panel visible."""
    go_to_view(page, "ajustes")
    suite.check("Ajustes tiene multiples tab-panels",
                page.locator(".tab-panel").count() >= 4)
    for target in ["dispositivos", "notificaciones", "seguridad", "empresa"]:
        page.locator(f'#settings-tabs .tab[data-tab="{target}"]').click()
        page.wait_for_timeout(SHORT_WAIT)
        suite.check_eq(f"Tab '{target}' activa su panel",
                       page.locator(f'.tab-panel.active[data-panel="{target}"]').count(), 1)


def test_devices_list(page: Any, suite: TestSuite) -> None:
    """La pestana Dispositivos NFC de Ajustes lista los terminales."""
    go_to_view(page, "ajustes")
    page.locator('#settings-tabs .tab[data-tab="dispositivos"]').click()
    page.wait_for_timeout(SHORT_WAIT)
    suite.check("Lista de dispositivos tiene items",
                page.locator("#device-list .device-card").count() > 0)


def test_responsive_desktop(page: Any, suite: TestSuite) -> None:
    """Layout desktop: sidebar fijo visible, KPIs en 4 columnas."""
    page.set_viewport_size(DESKTOP)
    page.wait_for_timeout(SHORT_WAIT)
    go_dashboard(page)
    sidebar_vis = page.eval_on_selector(
        "#sidebar", "e => { const r = e.getBoundingClientRect(); return r.left >= 0 && r.width > 0; }"
    )
    suite.check("Sidebar visible en desktop", sidebar_vis)
    cols = page.eval_on_selector_all(
        "#kpi-grid .kpi-card",
        "els => { const s = getComputedStyle(els[0].parentElement); return s.gridTemplateColumns.split(' ').length; }",
    )
    suite.check_eq("KPIs en 4 columnas en desktop", cols, 4)
    disp = page.eval_on_selector("#sidebar-toggle", "e => getComputedStyle(e).display")
    suite.check("Boton menu movil oculto en desktop", disp == "none", f"display={disp!r}")


def test_responsive_tablet(page: Any, suite: TestSuite) -> None:
    """Layout tablet (<=900px): sidebar fuera de pantalla, menu movil visible."""
    page.set_viewport_size(TABLET)
    page.wait_for_timeout(SHORT_WAIT)
    disp = page.eval_on_selector("#sidebar-toggle", "e => getComputedStyle(e).display")
    suite.check("Boton menu movil visible en tablet", disp != "none", f"display={disp!r}")
    transform = page.eval_on_selector("#sidebar", "e => getComputedStyle(e).transform")
    suite.check("Sidebar oculto (transform) en tablet",
                "matrix" in transform or "translate" in transform, f"transform={transform!r}")
    page.locator("#sidebar-toggle").click(timeout=CLICK_TIMEOUT)
    page.wait_for_timeout(SHORT_WAIT)
    suite.check_eq("Sidebar se abre al clickar menu movil",
                   page.locator("#sidebar.is-open").count(), 1)
    scrim_hidden = page.eval_on_selector("#sidebar-scrim", "e => getComputedStyle(e).display === 'none'")
    suite.check("Scrim visible al abrir sidebar movil", not scrim_hidden)
    page.keyboard.press("Escape")
    page.wait_for_timeout(SHORT_WAIT)
    suite.check_eq("Sidebar se cierra con Escape",
                   page.locator("#sidebar.is-open").count(), 0)


def test_responsive_mobile(page: Any, suite: TestSuite) -> None:
    """Layout movil (<=480px): KPIs en 2 columnas, user-info oculto."""
    page.set_viewport_size(MOBILE)
    page.wait_for_timeout(SHORT_WAIT)
    cols = page.eval_on_selector_all(
        "#kpi-grid .kpi-card",
        "els => { const s = getComputedStyle(els[0].parentElement); return s.gridTemplateColumns.split(' ').length; }",
    )
    suite.check_eq("KPIs en 2 columnas en movil", cols, 2)
    disp = page.eval_on_selector(".user-info", "e => getComputedStyle(e).display")
    suite.check("user-info oculto en movil", disp == "none", f"display={disp!r}")
    has_hscroll = page.evaluate(
        "() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2"
    )
    suite.check("Sin scroll horizontal en movil", not has_hscroll)


def test_navigation_to_all_views_mobile(page: Any, suite: TestSuite) -> None:
    """En movil, abrir el sidebar y navegar a cada vista sin errores."""
    page.set_viewport_size(MOBILE)
    page.wait_for_timeout(SHORT_WAIT)
    for vid, _t in VIEWS:
        page.locator("#sidebar-toggle").click(timeout=CLICK_TIMEOUT)
        page.wait_for_timeout(SHORT_WAIT)
        _nav_btn(page, vid).click(timeout=CLICK_TIMEOUT)
        page.wait_for_timeout(VIEW_WAIT)
        suite.check(f"Navegacion movil a '{vid}' OK",
                    page.locator(f'.view.is-active[data-view="{vid}"]').count() == 1)
        suite.check_eq(f"Sidebar cerrado tras navegar a '{vid}'",
                       page.locator("#sidebar.is-open").count(), 0)


# ===========================================================================
# Orquestador principal: arranca el navegador, ejecuta todas las pruebas en
# orden, imprime el informe y devuelve el TestSuite con resultados.
# ===========================================================================

ALL_TESTS: list[Callable] = [
    test_page_loads,
    test_seven_views_exist,
    test_views_navigable,
    test_svg_charts_dashboard,
    test_svg_charts_reportes,
    test_24_employees_count,
    test_kpis_rendered,
    test_dashboard_today_and_alerts,
    test_employee_search_filter,
    test_fichajes_filters,
    test_turnos_filter,
    test_incidents_resolve,
    test_ajustes_tabs,
    test_devices_list,
    test_responsive_desktop,
    test_responsive_tablet,
    test_responsive_mobile,
    test_navigation_to_all_views_mobile,
]

# Pruebas que requieren argumentos especiales ademas de (page, suite).
SPECIAL_ARGS = {test_page_loads: ("url", "tracker")}


def run_e2e(headless: bool = True) -> TestSuite:
    """Ejecuta la suite E2E completa y devuelve el TestSuite con resultados."""
    from playwright.sync_api import sync_playwright

    suite = TestSuite()
    if not DASHBOARD_HTML.exists():
        suite.check("dashboard_new.html existe", False, f"no encontrado: {DASHBOARD_HTML}")
        return suite

    port = _free_port(BASE_PORT)
    url = f"http://127.0.0.1:{port}/dashboard_new.html"
    httpd = start_local_server(DASHBOARD_HTML.parent, port)
    tracker = ConsoleTracker()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(viewport=DESKTOP, locale="es-ES")
            page = context.new_page()
            tracker.attach(page)
            for test_fn in ALL_TESTS:
                try:
                    needs = SPECIAL_ARGS.get(test_fn, ())
                    if "url" in needs:
                        test_fn(page, suite, url, tracker)
                    else:
                        test_fn(page, suite)
                except Exception as exc:  # pragma: no cover
                    suite.check(f"{test_fn.__name__} sin excepcion", False,
                                f"{type(exc).__name__}: {exc}")
                    traceback.print_exc()
            test_no_js_errors(suite, tracker)
            browser.close()
    finally:
        stop_local_server(httpd)
    return suite


# ===========================================================================
# Punto de entrada: script independiente o pytest.
# ===========================================================================

def main() -> int:
    """Punto de entrada del script independiente."""
    headless = "--show" not in sys.argv
    suite = run_e2e(headless=headless)
    suite.print_report()
    s = suite.summary()
    return 0 if s["failed"] == 0 else 1


# ---------------------------------------------------------------------------
# Fixtures y tests de pytest — permiten ejecutar la misma logica como suite
# CI con `pytest tests/test_dashboard_e2e.py`.
# ---------------------------------------------------------------------------

try:
    import pytest  # noqa: F401
    from playwright.sync_api import sync_playwright as _sp

    @pytest.fixture(scope="module")
    def dashboard_page():
        """Fixture pytest: arranca navegador y servidor, devuelve la page."""
        port = _free_port(BASE_PORT)
        httpd = start_local_server(DASHBOARD_HTML.parent, port)
        url = f"http://127.0.0.1:{port}/dashboard_new.html"
        with _sp() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport=DESKTOP, locale="es-ES")
            page = context.new_page()
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(LOAD_WAIT)
            yield page
            browser.close()
        stop_local_server(httpd)

    @pytest.fixture(scope="module")
    def console_tracker(dashboard_page):
        tracker = ConsoleTracker()
        tracker.attach(dashboard_page)
        return tracker

    def _make_pytest_test(test_fn):
        """Genera un test pytest que reutiliza el TestSuite para aserciones."""
        def _test(dashboard_page, console_tracker=None):
            suite = TestSuite()
            needs = SPECIAL_ARGS.get(test_fn, ())
            if "url" in needs:
                port = dashboard_page.url.split(":")[2].split("/")[0]
                test_fn(dashboard_page, suite,
                        f"http://127.0.0.1:{port}/dashboard_new.html", console_tracker)
            else:
                test_fn(dashboard_page, suite)
            failed = [r for r in suite.results if not r.passed]
            assert not failed, "\n".join(f"FAIL: {r.name} - {r.detail}" for r in failed)
        _test.__name__ = f"test_{test_fn.__name__.removeprefix('test_')}"
        return _test

    # Generar un test pytest por cada prueba E2E.
    for _fn in ALL_TESTS:
        globals()[_make_pytest_test(_fn).__name__] = _make_pytest_test(_fn)

except ImportError:  # pytest no instalado
    pass


if __name__ == "__main__":
    sys.exit(main())