# Gemischter synthetischer Mailbestand

Stand: 10. September 2026. Erweiterung der vorherigen MSG-Prüfung, ausschließlich
erfundene Daten. Keine Änderungen am Produktcode, keine neuen Abhängigkeiten.

## Umfang

- Zehn MSG-Varianten: bisherige vier Fälle, zusätzlich ANSI/Windows-1252,
  Emoji und mehrsprachiger Text, leere Felder, langer Body mit 5.000 Zeilen,
  drei Anlagen und formelähnlicher Betreff. Eine Erweiterung ist großgeschrieben.
- Zwölf EML-Varianten: UTF-8, ISO-8859-1, Base64, Quoted-Printable, reines HTML,
  Multipart-Alternative, vier Anlagen, leerer Body, fehlendes Datum,
  Antwortbezug, formelähnlicher Betreff und langer Body mit 5.000 Zeilen.
- Acht separate Negativproben: leere EML/MSG, ungültige MSG/PST, EML ohne Header,
  TXT, HTML und ein echtes synthetisches ZIP. Keine Outlook-Aufrufe für diese Tests.

Anlagen mit PDF-, XLSX-, PNG- und ZIP-Dateinamen sind Inventarproben mit
Text-/Binär-Platzhalterinhalt, keine validen Dokumente dieser Formate. Ihre Inhalte
werden vom Produkt nicht analysiert. Die Negativprobe `broken.pst` ist kein
gültiges PST-Archiv. Die tatsächliche PST-Abnahme bleibt offen.

## Erzeugung und automatisierte Prüfung

`scripts.generate_mail_corpus` verwendet `tests.corpus_samples`; der bestehende
MSG-Testschreiber wurde um ANSI-Eigenschaften und mehrere Anlagen erweitert.
Keine Nachrichtenwerte werden aus Produkt-Ausgaben als Sollwerte übernommen.
Der Generator schreibt ausschließlich in einen neuen Zielordner. Wiederholungen
erhalten eindeutige Message-IDs und getrennte Unterordner. Grenzen: 1..1000.

Vier neue Tests prüfen:

1. Alle 22 Dateien mit tatsächlichen Parsern: Betreff, ID, Datum, Absender,
   Empfänger, Body-Inhalt und Anlagen; alle positiven Vorprüfungen sind `ok`.
2. Fünf defekte Dateien werden in der Einzelvorprüfung als Fehler erkannt,
   drei nicht unterstützte als ignoriert. Die bekannte fehlende Inventarisierung
   ignorierter Dateien bei Ordnerläufen bleibt CHECK-02.
3. Gemischtes Analysepaket plus CSV, XLSX, XML und Markdown: JSON-Sollfelder,
   Parquet-ID-Menge, CSV-Zeilen und Formelpräfixe, XLSX-Zeilen und fehlende
   Formelzellen, XML-Nachrichtenanzahl und Markdown-Inhaltsprobe. Das ist keine
   vollständige Inhaltsgleichheitsprüfung aller sieben Formate; dokumentierte
   Formatverluste bleiben bestehen. Paketvalidierung läuft zusätzlich mit.
4. 550 echte Nachrichten, Import und Cachelauf: vollständige ID-Menge, null
   Parserfehler, 550 Quellen-Audits und Ergebnisindex-Seiten mit 500/50 Einträgen
   ohne Überschneidung. Dies prüft den Index, nicht die interaktive GUI-Navigation.

## Tatsächlich ausgeführter größerer Lauf

Bestand: `out/mixed-corpus-2026-09-10/input/` mit 250 MSG und 300 EML.
Sollwerte: `out/mixed-corpus-2026-09-10/expected.json`.
Analysepaket: `out/mixed-corpus-2026-09-10/output/runs/20260910T082622-0230d8b958664f01a455c1cd19436f96/`.

Ergebnis: `completed`, 550 Nachrichten, null Parserfehler. Eine separate
Rückleseprüfung verglich alle JSON-Nachrichten für Betreff, UTC-Datum,
Anlagennamen und -anzahl mit den Sollwerten, die Parquet-ID-Menge und sämtliche
elf Exportdateien anhand ihrer Manifestgrößen und SHA-256-Hashes.

Die abschließende unittest-Suite bestand mit 69 Tests in 18 Sekunden, ohne Skips.
Damit sind auch bestehende Python-GUI- und Architekturtests erfolgreich.
Kompilierung, `pip check`, `git diff --check` und lokale Dokumentations-Linkprüfung
bestanden; erzeugte MSG-Dateien und Sollwerte sind durch Git-Ausschlussregeln erfasst.
Kein neuer EXE-Build oder interaktiver EXE-Test: nur Testdatenwerkzeuge und
Dokumentation wurden geändert. Keine Testfenster gestartet, kein Commit/Push.

## Dokumentationsprüfung

README enthält Generatorbefehl und Grenzen, Architektur die Testzuständigkeiten,
STATUS die erweiterte Abdeckung und IMPORT-01 weiterhin teilweise. Datenmodell
und Projektziele benötigen keine Anpassung, weil Produktverhalten und Umfang
unverändert bleiben. Der frühere Bericht bleibt ein historischer Nachweis.
