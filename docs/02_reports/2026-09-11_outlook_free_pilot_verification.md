# Outlook-freier Pilotumfang und aktueller Windows-Build

Stand: 11. September 2026

## Auftrag und Festlegung

Der PST-Weg des ersten Piloten benötigt kein klassisches Outlook. Zum
Pilotumfang gehören EML, MSG und PST über das mitgelieferte libpff-Backend. Das
vorhandene Outlook-COM-Backend bleibt eine optionale Entwicklungsoption und ist
ohne eigene reale Abnahme kein freigegebener Pilotweg.

Geprüft wurden ausschließlich der öffentliche, bereits über SHA-256 festgelegte
PST-Testbestand sowie synthetische Testdaten. Reale Mailarchive wurden nicht
verarbeitet.

## Vergleichsbasis

- Windows 10, Python 3.11.9
- Anwendung `0.7.0-dev.1`
- Basisrevision `8d5de5a99187f9870f8bbf70b48e32763e6f88f0`
- korrigierter lokaler Quellbaum, im Build als `source_dirty: true` und mit
  `source_tree_sha256: d3273e703f61bdde649476b37715a113a8ea2bc5db3642595446c77a336c9bb9`
  ausgewiesen
- libpff-python-windows `20231205`
- PST-Prüfsumme
  `df01707f76d0e24ab913cf1ffeffa6eaf9c1d590e02102c7ed26bb3ac51d4e24`

## Gefundener und behobener EXE-Fehler

Der erste vollständig bediente EXE-Lauf erreichte die Verarbeitung, endete aber
mit einem Parserfehler. `pypff.open()` versuchte beim Auflösen des absoluten
Windows-Pfads auf das aktuelle Prozessarbeitsverzeichnis zuzugreifen; dieses war
in der gestarteten GUI-Sitzung nicht zugänglich. libpff meldete deshalb unter
anderem `unable to retrieve current working directory by volume`.

Der libpff-Adapter öffnet die PST nun selbst als binären Lesestrom und übergibt
ihn mit `pypff.open_file_object()`. Archiv und Dateistrom werden bei normalem
Ende, frühem Generatorabschluss und Öffnungsfehler geschlossen. Der zugehörige
Streamingtest prüft die Ressourcenfreigabe; der reale PST-Integrationstest
bestand nach der Änderung.

## Erfolgreiche Prüfungen

Der Standardlauf bestand 85 Tests; der optionale PST-Test wurde dort erwartbar
übersprungen. Separat mit gesetzter `MAILANALYST_PST_TEST_FILE` bestand der echte
libpff-Dateitest:

- zwei Nachrichten aus zwei erwarteten Ordnern,
- null Parserfehler,
- Analysepaket und Qualitätswarnungen,
- anschließender Cachelauf mit einem Cachetreffer auf Quellenebene,
- unveränderte SHA-256-Prüfsumme der PST.

`build_exe.ps1` erzeugte nach der Korrektur den Windows-Kandidaten erfolgreich.
Seine Buildmetadaten nennen die Basisrevision, den abweichenden lokalen
Quellbaum, Python 3.11.9 und `libpff-python-windows 20231205`. Das Paket enthält
`pypff.cp311-win_amd64.pyd`, `COPYING` und `COPYING.LESSER`; sein Manifest umfasst
2.588 Dateien. Größe und SHA-256 stimmten für alle 2.588 Manifesteinträge mit dem
Paket überein.

Der korrigierte Kandidat wurde anschließend vollständig in der Windows-GUI
bedient. Systemcheck, Datei- und Zielauswahl, Profil `Analysepaket`, ausdrücklich
gewähltes Backend `Ohne Outlook (libpff)`, Vorprüfung, Verarbeitung und Ergebnis
waren sichtbar. Zwei Läufe in dasselbe frische Ziel ergaben:

- Erstlauf: zwei Nachrichten, null Parserfehler, null Cachetreffer;
- Wiederholung: zwei Nachrichten, null Parserfehler, ein Cachetreffer;
- beide Quellenberichte: `verified_this_run`, Backend `libpff`;
- unveränderter PST-SHA-256 vor und nach den Läufen;
- je zwei konsistente Datensätze in JSON, Parquet und SQLite;
- je zwei gültige Markdown-Indexeinträge mit vorhandenen Dateien und Ankern;
- vollständige Übereinstimmung aller im Laufmanifest genannten Ausgabehashes.

Die Lauf-IDs lauten
`20260911T151607-c42491a846bb4b7689aed2f0464e5e02` und
`20260911T151630-f445e3f62f42405d8278f296c4b9e1e3`. Nur die gestartete
MailAnalyst-Testinstanz wurde danach geschlossen; es blieb kein Testfenster offen.

## Nicht als bestanden behauptet

Offen bleiben:

- ein selbst erzeugtes PST-Sollarchiv mit ausschließlich erfundenen Inhalten,
- ein ausdrücklich vom Netz getrennt ausgeführter Test,
- eine Wiederholung auf einem sauberen Windows-Testsystem,
- Fehler- und Abbruchtests mit einer gültigen PST,
- die spätere, nicht pilotkritische Realprüfung des Outlook-COM-Backends.

## Einordnung

DEC-02 ist hinsichtlich des Pilotumfangs entschieden und technisch im Paket
umgesetzt. Der lokale, vollständig bediente libpff-PST-EXE-Ablauf einschließlich
Cache ist bestanden. IMPORT-01, DATA-08 und REL-02 bleiben wegen des selbst
erzeugten Sollarchivs, gültiger PST-Fehler-/Abbruchtests sowie Offline- und
Zielsystemabnahme teilweise beziehungsweise offen. Der Echtdaten-Pilot und der
Umzug in die geschützte Umgebung wurden nicht gestartet.
