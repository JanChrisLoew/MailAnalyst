# UI-/UX-Review der Windows-GUI

Stand: 7. September 2026

## Auftrag und Ergebnis

Die bestehende Tkinter-Oberfläche wurde auf eine moderne, einfache und verständliche Benutzerführung ohne zusätzliche Effekte oder UI-Frameworks geprüft. Der fünfstufige Ablauf und die bestehende Farb- und Schriftgestaltung blieben erhalten. Auffällige Inkonsistenzen in Sprache, Hierarchie und Bedienhinweisen wurden unmittelbar korrigiert.

## Reviewbefunde und Korrekturen

- Sichtbare ASCII-Umschreibungen wie `pruefen`, `Zurueck` und `oeffnen` wirkten unfertig. Alle betroffenen GUI-Texte verwenden jetzt korrekte deutsche Zeichen.
- `WORKFLOW`, `Konfiguration` und `Daten festlegen` bezeichneten denselben Bereich unterschiedlich. Navigation und interne Schrittbezeichnung verwenden jetzt durchgehend `Ablauf` beziehungsweise `Daten & Ausgabe`.
- Die dreigeteilte Markenlinie im Kopf war rein dekorativ. Sie wurde durch eine einzelne schmale Primärlinie ersetzt; der Offline-Hinweis wurde typografisch beruhigt.
- Pfeil- und Aktualisierungssymbole in fast allen Aktionsbuttons erzeugten visuelle Unruhe. Die Buttons verwenden jetzt kurze, eindeutige Verben ohne dekorative Symbole.
- Die Auswahl in Vorprüfung und Ergebnisdetails war nur per Doppelklick erkennbar. Ein knapper Bedienhinweis und die Eingabetaste ergänzen die Bedienung.
- Die Ergebnisansicht bezeichnete den konkreten Laufordner als allgemeinen Zielordner. Text, Feldbezeichnung und Öffnen-Aktion sprechen jetzt eindeutig vom Laufordner.
- Technisch wirkende Statusketten mit senkrechten Strichen wurden in knapper lesbare, mit Mittelpunkt getrennte Zusammenfassungen umgestellt.
- Die sichtbaren Verarbeitungsphasen verwenden ebenfalls korrekte deutsche Bezeichnungen. Die frühere Schreibweise für vollständige URLs bleibt als interner Kompatibilitätswert akzeptiert.

## Verifikation

- 59 automatisierte Tests bestanden, einschließlich realem Tkinter-Ereignisablauf, Tastaturbindung, 50.000 Vorprüfungsquellen, 1.201 Ergebniszeilen, Fehlerfilter und Abbruch während des Exports.
- `compileall` für Paket, Tests und beide Einstiegsskripte war erfolgreich.
- `pip check` meldete keine defekten Abhängigkeiten.
- `git diff --check` meldete keine Whitespacefehler; die Hinweise betreffen nur die bestehende LF-/CRLF-Konvertierung unter Windows.
- Alle eigenen Python-Dateien bleiben unter der Grenze von 200 physischen Zeilen.
- Der PyInstaller-Build war erfolgreich. `dist/MailAnalyst/MailAnalyst.exe` startete aus `out/ui-start-check` mit dem Fenstertitel `MailAnalyst` und wurde anschließend sauber geschlossen.

## Interaktive Nachprüfung mit Computer Use

Die gebaute lokale Anwendung wurde anschließend mit Computer Use durch den vollständigen sichtbaren Ablauf bedient. Verwendet wurden zwei synthetische EMLs unter einem neuen ignorierten Testordner in `out/`.

- Der Systemcheck zeigte 13 erfolgreiche Prüfungen, eine optionale libpff-Warnung und keinen Fehler.
- Quelle und isolierter Zielordner ließen sich direkt eintragen; Konfiguration und primäre Aktion waren klar erkennbar.
- Die Vorprüfung zeigte zwei plausible EML-Quellen. Die neue Eingabetastenbedienung schaltete die markierte Quelle sichtbar zwischen `Ja` und `Nein` um.
- Verarbeitung, Exportphase, Quellenzahl, Nachrichtenzahl und Laufzeit waren verständlich sichtbar. Der Lauf endete mit zwei Quellen, zwei Nachrichten und null Parserfehlern.
- Nach manuellem Wechsel zur Ergebnisseite waren Laufordner, Zusammenfassung und beide Nachrichten sichtbar. Die Eingabetaste öffnete die Details der markierten Nachricht.
- `Neuer Lauf` führte mit erhaltenen Eingaben korrekt zurück zu `Daten & Ausgabe`.

Dabei wurden drei offene UX-Befunde reproduziert:

1. Nach erfolgreicher Verarbeitung markiert die Seitenleiste bereits `Ergebnis`, der Inhaltsbereich bleibt jedoch auf der abgeschlossenen Verarbeitungsseite. Erst ein weiterer Klick auf `Ergebnis` zeigt die Ergebnisansicht.
2. `Mindestens ein PST-Verarbeitungsweg` im Systemcheck und `Verarbeiten` in der Vorprüfung werden bei der Standardfensterbreite abgeschnitten. In der Ergebnisansicht ist die Statusspalte am rechten Rand ebenfalls nur teilweise sichtbar, obwohl sie zu den Kerninformationen gehört.
3. Der Nachrichtendialog erschien auf dem zweiten Monitor statt zentriert über dem MailAnalyst-Fenster. Die Tk-Dialoge erhalten derzeit kein explizites Elternfenster.

## Umsetzung und Schlussabnahme GUI-06

Die drei interaktiven Befunde wurden im selben Arbeitsblock behoben. Vor der programmgesteuerten Auswahl eines Schritts wird dessen Notebook-Seite nun aktiviert; dadurch wechseln Navigation und Ergebnisinhalt nach Abschluss gemeinsam. Die Breiten der Kernspalten in Systemcheck, Vorprüfung und Ergebnis wurden auf die verfügbare Standardbreite abgestimmt. Nachrichten-, Fehler- und Dateiauswahldialoge erhalten das Hauptfenster als explizites Elternfenster.

Der Mindestgrößentest deckte zusätzlich eine unterhalb des sichtbaren Bereichs liegende Konfigurationsaktion auf. Kompaktere vertikale Abstände halten `Vorprüfung starten` nun auch bei der festgelegten Mindestgröße von 980 × 640 Client-Pixeln sichtbar, ohne Elemente oder Optionen zu entfernen.

- 61 automatisierte Tests bestanden. Neue Regressionstests prüfen den tatsächlichen ausgewählten Ergebnis-Tab, Kernspaltenbreiten, Dialog-Elternfenster und die Erreichbarkeit der Konfigurationsaktion bei Mindestgröße.
- `compileall`, `pip check` und `git diff --check` waren erfolgreich; die Windows-Hinweise betreffen nur LF-/CRLF-Konvertierung. Alle eigenen Python-Dateien bleiben unter 200 physischen Zeilen.
- Der neu erstellte PyInstaller-Ordner unter `dist/MailAnalyst` wurde mit Computer Use geprüft. Bei Standardgröße waren die Kernüberschriften vollständig sichtbar. Nach der Verarbeitung von zwei synthetischen EMLs erschien die Ergebnisseite ohne weiteren Klick mit zwei Nachrichten und null Parserfehlern.
- Die Eingabetaste öffnete den Nachrichtendialog am Hauptfenster. Ergebnisansicht und horizontaler Scrollbalken blieben bei Mindestgröße bedienbar. Nach einem dabei gefundenen Abstandsproblem wurde erneut gebaut und dieselbe Mindestgrößenprüfung in `Daten & Ausgabe` erfolgreich wiederholt.
- Die unabhängige Rückleseprüfung bestätigte je zwei Datensätze in JSON, Parquet, Markdown-Index und Review-SQLite, übereinstimmende Message-IDs, vorhandene Monatsdateien und Anker, null Reviewfehler, einen Zielordner-Cache, Status `completed`, korrekte Exporthashes, zwei als `verified_this_run` gekennzeichnete Quellen sowie Log und Verarbeitungsoptionen.

Das optionale libpff blieb im Systemcheck die einzige Warnung; der geprüfte EML-Ablauf benötigt dieses Paket nicht. Alle von der Prüfung gestarteten GUI-Fenster wurden geschlossen.

## Grenzen

Die Computersteuerung ermöglichte die pixelbasierte Prüfung und einen vollständig bedienten synthetischen EXE-Lauf. Echte MSG-/PST-Archive, große Datenmengen, mehrere Windows-Skalierungsstufen und eine unabhängige Bedienperson waren nicht Teil dieser UI-/UX-Prüfung.
