import http.server, socketserver, threading
from playwright.sync_api import sync_playwright

root = r"C:/Users/jordi/talentup-fichaje/frontend"
handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=root, **kw)
httpd = socketserver.TCPServer(("127.0.0.1", 8772), handler)
t = threading.Thread(target=httpd.serve_forever, daemon=True); t.start()

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("PE: " + str(e)))
    page.goto("http://127.0.0.1:8772/dashboard_new.html", wait_until="networkidle")
    page.wait_for_timeout(2500)

    # --- Responsive: desktop ---
    sidebar_vis = page.eval_on_selector("#sidebar", "e=>{const r=e.getBoundingClientRect(); return r.left>=0 && r.width>0}")
    print("desktop sidebar visible:", sidebar_vis)
    kpi_cols = page.eval_on_selector_all("#kpi-grid .kpi-card", "els=>{const s=getComputedStyle(els[0].parentElement); return s.gridTemplateColumns.split(' ').length}")
    print("desktop kpi cols:", kpi_cols)
    mobile_btn_disp = page.eval_on_selector("#sidebar-toggle", "e=>getComputedStyle(e).display")
    print("desktop sidebar-toggle display:", mobile_btn_disp)

    # --- Responsive: tablet (900px) ---
    page.set_viewport_size({"width": 900, "height": 1024})
    page.wait_for_timeout(400)
    mobile_btn_disp_t = page.eval_on_selector("#sidebar-toggle", "e=>getComputedStyle(e).display")
    print("tablet sidebar-toggle display:", mobile_btn_disp_t)
    sidebar_transform = page.eval_on_selector("#sidebar", "e=>getComputedStyle(e).transform")
    print("tablet sidebar transform:", sidebar_transform)
    page.locator("#sidebar-toggle").click(timeout=5000)
    page.wait_for_timeout(400)
    print("tablet sidebar is-open:", page.locator("#sidebar.is-open").count())
    scrim_disp = page.eval_on_selector("#sidebar-scrim", "e=>getComputedStyle(e).display")
    print("tablet scrim display when open:", scrim_disp)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    print("tablet sidebar after Escape:", page.locator("#sidebar.is-open").count())

    # --- Responsive: mobile (375px) ---
    page.set_viewport_size({"width": 375, "height": 720})
    page.wait_for_timeout(400)
    kpi_cols_m = page.eval_on_selector_all("#kpi-grid .kpi-card", "els=>{const s=getComputedStyle(els[0].parentElement); return s.gridTemplateColumns.split(' ').length}")
    print("mobile kpi cols:", kpi_cols_m)
    user_info_disp = page.eval_on_selector(".user-info", "e=>getComputedStyle(e).display")
    print("mobile user-info display:", user_info_disp)
    has_hscroll = page.evaluate("()=>document.documentElement.scrollWidth > document.documentElement.clientWidth + 2")
    print("mobile horizontal scroll:", has_hscroll)

    # Mobile navigation to each view
    for vid in ["dashboard", "empleados", "fichajes", "turnos", "reportes", "incidencias", "ajustes"]:
        page.locator("#sidebar-toggle").click(timeout=5000)
        page.wait_for_timeout(300)
        page.locator('#nav-list .nav-item[data-view="' + vid + '"]').click(timeout=5000)
        page.wait_for_timeout(700)
        active = page.locator('.view.is-active[data-view="' + vid + '"]').count()
        still_open = page.locator("#sidebar.is-open").count()
        print("mobile nav", vid, "-> active:", active, "sidebar still open:", still_open)

    # --- Back to desktop for interaction tests ---
    page.set_viewport_size({"width": 1440, "height": 900})
    page.wait_for_timeout(400)

    # --- Fichajes filters ---
    page.locator('#nav-list .nav-item[data-view="fichajes"]').click(timeout=5000)
    page.wait_for_timeout(700)
    cnt_all = page.locator("#cnt-all").inner_text()
    print("cnt-all:", cnt_all)
    chip_ok = page.locator('#fichaje-filters .chip-filter[data-filter="ok"]')
    print("chip ok count:", chip_ok.count())
    if chip_ok.count():
        chip_ok.click()
        page.wait_for_timeout(300)
        print("chip ok active:", page.locator('#fichaje-filters .chip-filter[data-filter="ok"].active').count())
        page.locator('#fichaje-filters .chip-filter[data-filter="all"]').click()
        page.wait_for_timeout(300)
        print("chip all active:", page.locator('#fichaje-filters .chip-filter[data-filter="all"].active').count())

    # --- Turnos filter ---
    page.locator('#nav-list .nav-item[data-view="turnos"]').click(timeout=5000)
    page.wait_for_timeout(700)
    print("schedule-table:", page.locator(".schedule-table").count())
    sel = page.locator("#turno-filter-area")
    print("turno-filter-area count:", sel.count())
    if sel.count():
        sel.select_option("Cocina")
        page.wait_for_timeout(300)
        sel.select_option("todos")
        page.wait_for_timeout(300)

    # --- Incidents resolve ---
    page.locator('#nav-list .nav-item[data-view="incidencias"]').click(timeout=5000)
    page.wait_for_timeout(700)
    print("incident-card:", page.locator("#incident-list .incident-card").count())
    before = page.locator("#toast-container .toast").count()
    rb = page.locator("[data-resolve]").first
    if rb.count():
        rb.click()
        page.wait_for_timeout(400)
        after = page.locator("#toast-container .toast").count()
        print("toasts before/after:", before, after)
    page.locator('#incident-tabs .tab[data-incident-tab="resuelta"]').click()
    page.wait_for_timeout(400)
    print("resolved tab incident-card:", page.locator("#incident-list .incident-card").count())

    # --- Ajustes tabs ---
    page.locator('#nav-list .nav-item[data-view="ajustes"]').click(timeout=5000)
    page.wait_for_timeout(700)
    print("tab-panel count:", page.locator(".tab-panel").count())
    for tgt in ["dispositivos", "notificaciones", "seguridad", "empresa"]:
        page.locator('#settings-tabs .tab[data-tab="' + tgt + '"]').click()
        page.wait_for_timeout(300)
        print("tab", tgt, "active panel:", page.locator('.tab-panel.active[data-panel="' + tgt + '"]').count())

    # --- Form empresa submit ---
    page.locator('#settings-tabs .tab[data-tab="empresa"]').click()
    page.wait_for_timeout(300)
    before = page.locator("#toast-container .toast").count()
    page.locator("#form-empresa button[type='submit'], #form-empresa .btn-primary").first.click()
    page.wait_for_timeout(500)
    after = page.locator("#toast-container .toast").count()
    print("form empresa toasts before/after:", before, after)

    # --- Employee search ---
    page.locator('#nav-list .nav-item[data-view="empleados"]').click(timeout=5000)
    page.wait_for_timeout(700)
    page.locator("#emp-search").fill("Laia")
    page.wait_for_timeout(400)
    print("search Laia rows:", page.locator("#emp-tbody tr").count())
    page.locator("#emp-search").fill("")
    page.wait_for_timeout(300)
    page.locator("#emp-filter-area").select_option("Cocina")
    page.wait_for_timeout(300)
    cocina = page.locator("#emp-tbody tr").count()
    print("cocina rows:", cocina)
    page.locator("#emp-filter-area").select_option("todos")
    page.wait_for_timeout(300)
    print("restored rows:", page.locator("#emp-tbody tr").count())

    # toggle to tarjetas
    page.locator('#emp-view-toggle button[data-emp-view="tarjetas"]').click()
    page.wait_for_timeout(400)
    print("emp-tile count:", page.locator("#emp-view-tarjetas .emp-tile").count())
    page.locator('#emp-view-toggle button[data-emp-view="tabla"]').click()
    page.wait_for_timeout(300)

    print("JS ERRORS:", errs[:10])
    b.close()
httpd.shutdown()