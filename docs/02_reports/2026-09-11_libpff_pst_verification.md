# libpff-PST-Dateiprüfung vom 11. September 2026

## Zweck und Einordnung

Dieser Arbeitsblock prüft erstmals den tatsächlichen libpff-Dateipfad mit einer
gültigen PST. Er ist ein technischer Referenznachweis für IMPORT-01 und DATA-08,
aber keine vollständige 0.7.0-Abnahme: Die Datei wurde nicht von MailAnalyst
synthetisch erzeugt, das Outlook-Backend wurde nicht ausgeführt und DEC-02 bleibt
offen. Es wurden keine persönlichen oder projektbezogenen Mailbestände verwendet.

## Referenzdatei und Laufzeit

- Quelle: `libyal/testdata`, Datei `pst/outlook.pst`
- Inhalt: herstellerseitige Outlook-2003-Willkommensnachricht, zweimal in
  unterschiedlichen Ordnern; keine persönlichen Postfachdaten
- Größe: 271.360 Bytes
- SHA-256: `df01707f76d0e24ab913cf1ffeffa6eaf9c1d590e02102c7ed26bb3ac51d4e24`
- Python-Paket: `libpff-python-windows==20231205`
- Wheel-SHA-256: `532aa36d9ad3d983a4349235cba2acff393759adfbfaed54f9c400be339d3e0b`

Die PST wird nicht eingecheckt. `scripts/fetch_pst_test_fixture.py` lädt sie an
einen expliziten neuen Pfad und prüft die festgelegte Prüfsumme.
`requirements-pst-test.txt` hält das optionale Windows-Wheel mit Hash getrennt
von Standardinstallation, Windows-Lockdatei und Build.

Die Referenz stammt aus dem öffentlichen
[libyal-Testdaten-Repository](https://github.com/libyal/testdata/tree/main/pst);
libpff selbst verweist in seinem
[Synchronisationsskript](https://github.com/libyal/libpff/blob/main/synctestdata.ps1)
auf diesen Bestand.

## Geprüfte Sollwerte

Der vollständige Servicepfad mit Profil `Analysepaket` und Backend
`Ohne Outlook (libpff)` lieferte:

- zwei Nachrichten, null Parserfehler;
- Betreff `Welcome to Microsoft Office Outlook 2003`;
- Versandzeit `2007-04-29T22:27:33.593000+00:00`;
- Ordner `Top of Personal Folders\Inbox` und
  `Top of Personal Folders\Recovered_Group2`;
- Backendbezug `libpff` und leere, nicht erfundene Empfängeradressen;
- zwei `unresolved_email`-Qualitätswarnungen für die fehlende Absenderadresse;
- beim zweiten Lauf einen Quell-Cachetreffer mit erneut zwei Nachrichten.

Vor dem ersten und nach dem zweiten Lauf wurde die Quelldatei erneut gehasht.
Beide Werte entsprechen der festgelegten Prüfsumme; der lesende Import hat die
PST somit in diesem Erfolgs- und Cachefall nicht verändert.

## Automatisierung und Grenzen

`tests/test_pst_file.py` läuft nur bei gesetztem
`MAILANALYST_PST_TEST_FILE` und installiert oder lädt nichts selbst. Ohne Datei
oder pypff wird er übersprungen. Der normale Testlauf und der ausgelieferte Build
bleiben dadurch unabhängig vom Drittanbieter-Wheel.

Der lokale Standardlauf bestand am PST-/RTF-Zwischenstand 83 Tests; der optionale
PST-Test wurde dabei erwartungsgemäß einmal übersprungen. Mit installiertem
Test-Wheel bestand der PST-Test zuvor separat, sodass alle 84 vorhandenen
Testfälle ausgeführt und erfolgreich waren. Der RTF-Fall ist Teil des grünen
Standardlaufs. Zusätzlich bestanden Python-Kompilierung, `pip check`, die
gehashte optionale Requirements-Prüfung und die lokale Dokumentations-Linkprüfung.
Nach Abschluss der Dateiprüfung wurde das optionale libpff-Wheel wieder aus der
Standard-Entwicklungsumgebung entfernt; `pip check` blieb erfolgreich.

Nicht nachgewiesen sind ein selbst erzeugtes synthetisches PST-Archiv mit frei
definierten Empfängern und Anlagen, weitere PST-Versionen und Schäden, das
Outlook-Backend, Quellschutz bei Fehler oder Abbruch sowie ein EXE-Lauf mit
gebündeltem libpff. Das Wheel wird vor einer möglichen Auslieferung gesondert
zu bewerten und abzunehmen sein; der erfolgreiche Entwicklungstest entscheidet
DEC-02 nicht vorweg.

## Ergänzende MSG-Prüfung

Der synthetische MSG-Bestand wurde im selben Arbeitsblock von vier auf sechs
Dateien erweitert. Die neue Datei besitzt keinen Klartext- oder HTML-Body,
sondern ausschließlich einen gültigen komprimierten RTF-Stream mit erfundenem
Inhalt. Der tatsächliche `extract-msg`-Pfad liest den Umlauttext, Datum,
Absender und Empfänger korrekt; Analysepaket und anschließender Cachelauf
enthielt zunächst fünf Nachrichten ohne Parserfehler. Eine sechste MSG enthält
eine echte eingebettete Nachricht als OLE-Unterstruktur. `extract-msg` öffnet
deren inneren Betreff, Absender und Text; MailAnalyst hält im Masterexport Namen
und `embedded_attachment_count = 1` fest. Weil der innere Inhalt noch nicht
exportiert wird, entsteht die strukturierte Warnung
`embedded_message_not_extracted`. Analysepaket und Cachewiederholung bestanden
mit sechs Nachrichten und ohne Parserfehler. Der separate gemischte 550er-
Regressionsbestand bleibt unverändert.

Mit dieser Erweiterung trägt der Entwicklungskandidat die Version
`0.7.0-dev.1`, der Nachrichtenvertrag Version 2 und der Parser Revision 3.
Der abschließende Standardlauf bestand 85 Tests mit einem erwarteten optionalen
PST-Skip. Ein neuer EXE-Build wurde in diesem Arbeitsblock nicht erstellt.

## Tkinter-Testprozess

Während eines ersten Gesamtlaufs erschien ein nativer `python.exe`-Fehlerdialog
mit `0x80000003`. Das Prozessprotokoll zeigte unmittelbar zuvor
`Tcl_AsyncDelete: async handler deleted by the wrong thread`: Nach zerstörten
Testfenstern verblieben Python-Referenzen auf Tk-Variablen, die erst während
eines späteren Parserworker-Laufs eingesammelt wurden.

Die gemeinsame GUI-Testbereinigung setzt die App-Referenz nach `destroy()` nun
zurück und führt `gc.collect()` noch im GUI-Thread aus. Der Sonderfall eines
bereits durch die getestete Schließlogik zerstörten Fensters verwendet dieselbe
threadgebundene Freigabe. Anschließend bestanden erst 15 GUI-Tests, dann der
kritische Ablauf aus GUI-Tests und Mail-Korpus mit 19 Tests sowie zweimal der
vollständige Standardlauf mit je 83 Tests und einem erwarteten optionalen
PST-Skip. Alle Prozesse endeten mit Exitcode 0; der Tcl-Abbruch trat nicht erneut
auf. Diese Änderung betrifft ausschließlich die Testbereinigung, nicht den
Produkt-Lifecycle der GUI.
