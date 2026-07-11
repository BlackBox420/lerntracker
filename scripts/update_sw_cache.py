#!/usr/bin/env python3
"""Schreibt einen Content-Hash über alle SHELL-Dateien als neue CACHE-Version
in sw.js. Wird vom pre-commit-Hook aufgerufen, sobald eine SHELL-Datei Teil
eines Commits ist — kein manuelles Hochzählen der Versionsnummer mehr nötig.

Der Hash muss als Literal in sw.js LANDEN (nicht nur zur Laufzeit berechnet
werden), weil Browser ein Service-Worker-Update ausschliesslich per
Byte-Vergleich der sw.js-Datei selbst erkennen, nicht daran, was sie zur
Laufzeit tut. Identisches Skript wie im Schwester-Repo (General).
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SW_PATH = ROOT / "sw.js"


def main():
    sw_text = SW_PATH.read_text()

    shell_match = re.search(r"const SHELL\s*=\s*(\[[\s\S]*?\]);", sw_text)
    if not shell_match:
        print("update_sw_cache: SHELL-Array in sw.js nicht gefunden", file=sys.stderr)
        return 1
    shell_entries = re.findall(r"'([^']+)'", shell_match.group(1))

    hasher = hashlib.sha256()
    seen = set()
    for entry in shell_entries:
        rel = entry.lstrip("./") or "index.html"
        if rel in seen:
            continue
        seen.add(rel)
        path = ROOT / rel
        if not path.is_file():
            continue
        hasher.update(path.read_bytes())
    new_hash = hasher.hexdigest()[:12]

    cache_match = re.search(r"const CACHE\s*=\s*'([^']+)'", sw_text)
    if not cache_match:
        print("update_sw_cache: CACHE-Konstante in sw.js nicht gefunden", file=sys.stderr)
        return 1
    old_value = cache_match.group(1)
    prefix = re.sub(r"[^-]+$", "", old_value)  # alles bis zum letzten '-' inkl.
    new_value = f"{prefix}{new_hash}"

    if new_value == old_value:
        return 0  # Inhalt unveraendert, kein neuer Cache noetig

    new_sw_text = sw_text[: cache_match.start(1)] + new_value + sw_text[cache_match.end(1):]
    SW_PATH.write_text(new_sw_text)
    print(f"update_sw_cache: CACHE aktualisiert {old_value} -> {new_value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
