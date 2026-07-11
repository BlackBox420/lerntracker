#!/usr/bin/env python3
"""Smoke-Test: lädt die echte App und klickt (per direktem Funktionsaufruf,
nicht per simuliertem DOM-Klick — schneller und robuster gegen CSS-Änderungen)
durch alle Haupt-Tabs und Modals, prüft dabei nur EINE Sache — wirft dabei
IRGENDWO ein unerwarteter JS-Fehler? Direkter Anlass: ein TypeError beim
Rendern der Übersicht (getStreak()/getWeeklyRecap() gegen einen alten
HISTORY-Eintrag ohne reviewsDone-Feld, siehe der entsprechende Fix weiter
oben in dieser Datei) — genau diese Art Fehler (Rendering + eine bestimmte,
z.B. veraltete Datenform) hätte eine rein isolierte Logik-Prüfung nicht
gefangen.

Siehe scripts/_test_harness.py für das WARUM (Browser statt Node).

Aufruf: python3 scripts/test_smoke.py
Voraussetzung: `pip install playwright && playwright install chromium` einmalig.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _test_harness import run_js_tests, report  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Kein loadDemoData() in diesem Repo (Single-file, persönliche Version) — beim
# ersten Laden ohne localStorage greifen automatisch die SEED_SUBJECTS/
# SEED_TOPICS aus dem Quellcode selbst, das reicht für einen realistischen
# Smoke-Test völlig aus.
SETUP_JS = r"""
() => {
  // Regressionsfall für den genau hier gefundenen Bug: ein alter Tageseintrag
  // ganz ohne reviewsDone-Feld, wie er vor dessen Einführung geschrieben
  // wurde bzw. von einem Sync mit älterem Code kommen kann. Muss weiterhin
  // klaglos durch getStreak()/getWeeklyRecap() laufen.
  HISTORY['2020-01-01'] = {reviewsDue: 3, subjPct: {}};
  localStorage.setItem('lt-history', JSON.stringify(HISTORY));
}
"""

TESTS_JS = r"""
() => {
  const results = [];
  function checkNoThrow(name, fn) {
    try {
      fn();
      results.push({name, pass: true});
    } catch (e) {
      results.push({name, pass: false, actual: e.message});
    }
  }

  checkNoThrow('Tab: Übersicht', () => setTab('overview'));
  checkNoThrow('Tab: Karteikarten', () => setTab('cards'));
  checkNoThrow('Tab: Statistik', () => setTab('stats'));
  checkNoThrow('Tab: zurück zu Übersicht', () => setTab('overview'));

  checkNoThrow('Tagesplan-Modal öffnen', () => openPlan());
  checkNoThrow('Tagesplan: Tab "Morgen"', () => setPlanDay(1));
  checkNoThrow('Tagesplan: Tab "Heute"', () => setPlanDay(0));
  checkNoThrow('Tagesplan: Ansicht "Ideal"', () => setPlanView('ideal'));
  checkNoThrow('Tagesplan: Ansicht "Angepasst"', () => setPlanView('adapted'));
  checkNoThrow('Tagesplan-Modal schließen', () => closePlan());

  checkNoThrow('Verwalten-Modal öffnen', () => openManage());
  checkNoThrow('Verwalten-Modal schließen', () => closeManage());

  checkNoThrow('Motivation/Sync-Modal öffnen', () => openModal());
  checkNoThrow('Motivation/Sync-Modal schließen', () => closeModal());

  checkNoThrow('Hilfe-Modal öffnen', () => openHelp());
  checkNoThrow('Hilfe-Modal schließen', () => closeHelp());

  // Nochmal Übersicht nach allem hin und her — deckt Nachwirkungen ab (z.B.
  // ein Modal, das globalen State kaputt hinterlässt).
  checkNoThrow('Tab: Übersicht (erneut, nach allen Modals)', () => setTab('overview'));

  return results;
}
"""


def main():
    results, load_errors = run_js_tests(ROOT, TESTS_JS, SETUP_JS)
    if load_errors:
        print("JS-Fehler beim Laden der App:")
        for e in load_errors:
            print(" ", e)
        return 1
    return report(results)


if __name__ == "__main__":
    sys.exit(main())
