import http.server, socketserver, threading, time
from playwright.sync_api import sync_playwright
root = r"C:/Users/jordi/talentup-fichaje/frontend"
handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=root, **kw)
httpd = socketserver.TCPServer(("127.0.0.1", 8766), handler)
t = threading.Thread(target=httpd.serve_forever, daemon=True); t.start()
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_context(viewport={"width":1440,"height":900}).new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.on("console", lambda m: errs.append(f"console.{m.type}: {m.text}") if m.type=="error" else None)
    r = page.goto("http://127.0.0.1:8766/dashboard_new.html", wait_until="networkidle")
    page.wait_for_timeout(3000)
    print("STATUS:", r.status if r else None)
    print("TITLE:", page.title())
    print("NAV-LIST exists:", page.locator("#nav-list").count())
    print("nav-item count:", page.locator(".nav-item").count())
    print("nav-item with data-view count:", page.locator('.nav-item[data-view]').count())
    print("sidebar exists:", page.locator("#sidebar").count())
    ni = page.locator('.nav-item').first
    if ni.count():
        print("FIRST nav-item outerHTML:", ni.evaluate("e=>e.outerHTML")[:200])
    print("view count:", page.locator(".view").count())
    print("JS ERRORS:", errs[:10])
    b.close()
httpd.shutdown()