"""Gemeinsame Test-Infrastruktur für die Browser-basierten Unit-Tests dieses
Repos (test_schedule_core.py, test_score.py, ...).

Warum über den Browser statt Node: das Projekt hat bewusst kein Node/npm im
Toolchain (kein Build-Schritt, siehe CLAUDE.md), auf dem Entwicklungsrechner
ist auch gar kein Node installiert. Die zu testende Logik ist zudem als
normales globales <script> geschrieben (kein module.exports), hängt also an
echten Browser-Globals (calcScore, S_MAP, tr, localStorage, ...) aus den
Schwester-Dateien. Anstatt das alles in Node nachzubauen/zu mocken, läuft der
Test in der echten App in einem echten (headless) Chrome via Playwright.
"""
import http.server
import socket
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def serve(root, port):
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(root), **kw)
    httpd = http.server.ThreadingHTTPServer(("localhost", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def run_js_tests(root: Path, tests_js: str, setup_js: str = ""):
    """Lädt die echte App headless, führt optional setup_js aus (z.B. um
    deterministische Fixture-Daten in die globalen State-Variablen zu
    schreiben) und wertet dann tests_js aus. tests_js muss ein Array von
    {name, pass, [actual, expected]}-Objekten zurückgeben.

    Gibt (results, load_errors) zurück — load_errors ist nur nicht-leer, wenn
    schon das Laden der App selbst fehlschlägt (dann ist results leer).

    Pageerrors, die WÄHREND tests_js auftreten (z.B. asynchron aus einem
    setTimeout/Promise heraus, nicht per try/catch in tests_js selbst
    abgefangen), landen zusätzlich als eigene fehlgeschlagene Einträge in
    results — wichtig für Smoke-Tests, die reale UI-Funktionen aufrufen statt
    nur reine, synchrone Funktionen zu prüfen.
    """
    port = free_port()
    httpd = serve(root, port)
    url = f"http://localhost:{port}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.goto(url, wait_until="networkidle")
        page.evaluate("if (typeof setLang === 'function') setLang('de')")
        if setup_js:
            page.evaluate(setup_js)
        page.wait_for_timeout(100)

        if errors:
            browser.close()
            httpd.shutdown()
            return [], errors

        errors_before = len(errors)
        results = page.evaluate(tests_js)
        page.wait_for_timeout(200)  # kurz warten auf verzögerte/asynchrone Fehler
        for err in errors[errors_before:]:
            results.append({"name": f"unerwarteter Laufzeitfehler: {err}", "pass": False})
        browser.close()

    httpd.shutdown()
    return results, []


def report(results):
    """Druckt alle Ergebnisse aus und gibt den passenden Prozess-Exitcode zurück."""
    failed = [r for r in results if not r["pass"]]
    for r in results:
        mark = "ok" if r["pass"] else "FAIL"
        print(f"[{mark}] {r['name']}")
        if not r["pass"] and "actual" in r:
            print(f"       erwartet={r.get('expected')!r} erhalten={r.get('actual')!r}")
    print(f"\n{len(results)-len(failed)}/{len(results)} Tests bestanden.")
    return 1 if failed else 0
