# Synthetische MSG-/PST-Importprüfung

Stand: 10. September 2026. Umfang: echte Dateiformate mit erfundenen Inhalten,
keine Verarbeitung realer Postfächer, kein Commit oder Push.

## Testbestand und Vergleichsbasis

`tests/msg_samples.py` schreibt vier Unicode-MSG-Dateien zur Laufzeit mit
`extract_msg.ole_writer.OleWriter`. Nur der CFB-Schreiber der Bibliothek wird
verwendet; Nachrichtenwerte und Sollwerte sind fest vorgegeben, keine aus dem
MailAnalyst-Ergebnis übernommenen Snapshots. Der echte `extract-msg`-Parser liest
die Dateien ohne Testdouble. Container-Schreiber und Parser stammen aus derselben
Bibliothek; eine unabhängige Outlook-Kompatibilitätsabnahme ist dies nicht.

| Fall | Geprüfter Inhalt |
| --- | --- |
| plain | Unicode-Betreff/Klartext, Absender, To/CC, Message-ID, UTC-Monatswechsel |
| html | HTML ohne Plaintext, Textableitung, eine benannte Anlage, Winterzeitwechsel |
| reply | In-Reply-To und References, Sommerzeitwechsel |
| undated | Fehlendes Versanddatum bleibt leer |

Zusätzlich wird eine MSG-Datei abgeschnitten; der Dispatcher muss einen Fehler
mit Herkunft liefern und den Dateizugriff freigeben. Analysepaket und Cachelauf
prüfen JSON/Parquet-Inhalte, Nachrichtenanzahl, IDs, Abschlussstatus und Quellen-Audits.
Ein separater Test prüft, dass Parserrevision 1 einen Neuimport auslöst.
Die bestehende Markdown-Paketvalidierung läuft beim Analysepaket mit.

## Befund und Korrektur

Der reale Parser liefert das MSG-Versanddatum als `datetime`. MailAnalyst wandelte
es bisher in Text um und übergab die ISO-Darstellung an einen RFC-Maildatumsparser.
Dadurch blieb `sent_at_utc` trotz vorhandenen Datums leer. Die neuen Dateitests
reproduzierten dies für drei bekannte Zeitpunkte vor der Korrektur.

`parsing/msg.py` übernimmt `datetime` nun direkt, erhält einen vorhandenen Offset
und normalisiert nach UTC. Naive Werte werden wie bisher beabsichtigt als UTC
interpretiert; textuelle Werte verwenden weiterhin den bestehenden Parser.
Die globale Parserrevision wurde von 1 auf 2 erhöht. Bestehende Caches werden
deshalb neu importiert; es handelt sich nicht um eine Änderung des Exportschemas.

Beim Aufbau des Testgenerators fehlten zunächst leere Named-Property-Streams.
Dies war ein Fixturefehler und wurde am Generator korrigiert, nicht durch eine
Lockerung des Produktparsers oder der Sollwerte.

## Ausgeführte Prüfungen

Umgebung: Windows, Python 3.11.9, extract-msg 0.56.1, Projekt-venv.

- Abschließende vollständige unittest-Suite: 65 Tests erfolgreich in 11,8 Sekunden,
  einschließlich Python-Tkinter-Tests und vier neuer MSG-Tests, keine übersprungenen Tests.
- Gezielte MSG- und Architekturprüfung: sechs Tests erfolgreich.
- `compileall` für Paket, Tests, Skripte und Einstiegspunkte erfolgreich.
- `pip check`: keine beschädigten Abhängigkeiten.
- `build_exe.ps1`: Windows-Build erfolgreich.
- Dokumentationsverweise: alle lokalen Linkziele der betroffenen Dokumente vorhanden.
- Generator tatsächlich ausgeführt: `out/synthetic-msg-2026-09-10/input/` und
  `out/synthetic-msg-2026-09-10/expected.json`; sämtliche erzeugten Daten ignoriert.

## PST und weitere Grenzen

`pypff` ist lokal nicht installiert. `win32com` und die Outlook-COM-Registrierung
sind vorhanden. Ein `Dispatch('Outlook.Application')`-Aufruf kehrte nicht zurück
und wurde abgebrochen. Ein separater `GetActiveObject`-Versuch meldete
`0x800401E3` (Vorgang nicht verfügbar). Keine PST wurde erzeugt oder gelesen;
bestehende Postfächer wurden nicht geöffnet oder inventarisiert. Die Registrierung
allein bestätigt keinen nutzbaren Outlook-Importweg.
Bei der abschließenden Prozessprüfung war keine Outlook-Instanz mehr vorhanden;
es wurden keine Testfenster offengelassen.

PST-Testdoubles bleiben weiterhin reine Tests der Adapterlogik. Noch offen sind
ein betriebsbereites klassisches Outlook für einen separaten synthetischen Store
oder ein anderer geprüfter PST-Erzeuger sowie ein verfügbares libpff-Backend.
Danach sind Sollfelder, Ordnerrekursion, Hashstabilität und Store-Lifecycle mit
derselben synthetischen PST über beide Importwege zu prüfen.

ANSI-MSG, RTF-Sonderfälle, eingebettete Nachrichten, Exchange-Auflösung und
repräsentative historische Archive sind nicht durch diese vier Dateien abgedeckt.
Keine erneute interaktive EXE-Bedienprüfung: In dieser Sitzung steht kein
aufrufbarer nativer Computer-Use-Node-Runtime zur Verfügung. Build und Python-GUI-
Tests sind keine vollständige EXE-Funktionsabnahme.

## Dokumentationsprüfung

README um Generator und tatsächliche Testabdeckung ergänzt; Architektur um
Testzuständigkeiten; Datenmodell um MSG-Datumssemantik und Parserrevision;
STATUS mit IMPORT-01 teilweise und offenem PST-Nachweis aktualisiert.
Projektziele bleiben unverändert. Historische Abnahmeberichte bleiben historisch.

Formatreferenz: [Microsoft MS-OXMSG](https://learn.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-oxmsg/621801cb-b617-474c-bce6-69037d73461a).
