# MailAnalyst – vollständiger Repository-Review

Stand: 4. September 2026

## 1. Zweck dieses Berichts

Dieser Bericht dokumentiert den technischen und fachlichen Stand von MailAnalyst. Er dient als Arbeitsgrundlage für die nächste Entwicklungsphase.

Geprüft wurden:

- Parser für EML, MSG und PST
- Cache- und Hashlogik
- CSV-, Excel-, JSON-, XML-, Parquet- und Markdown-Exporte
- Markdown-Monatsdatensatz und Suchindex
- Systemcheck und Dateivorprüfung
- grafischer Fünf-Schritt-Workflow
- lokaler und offlinefähiger Betrieb
- portable Windows-EXE
- Abhängigkeiten und Dokumentation
- Eignung für große, beweisrelevante Mailarchive

Bei diesem Review wurden keine funktionalen Änderungen vorgenommen.

## 2. Gesamturteil

MailAnalyst ist ein funktionierender und verständlich aufgebauter Prototyp. Kleine EML-Datenmengen können lokal eingelesen und in alle vorgesehenen Ausgabeformate geschrieben werden. Die GUI führt nachvollziehbar durch Systemcheck, Konfiguration, Vorprüfung, Verarbeitung und Ergebnis. Der Workflow benötigt zur Laufzeit keine Cloud-API.

Für den geplanten Einsatz mit mehrjährigen Mailarchiven und beweisrelevanten Daten ist die Anwendung noch nicht produktionsreif. Die größten Risiken betreffen:

1. Speicherverbrauch und Skalierbarkeit
2. Ablage und Sicherheit des Caches
3. Nachweiswert der gespeicherten Hashes
4. konkurrierende GUI-Läufe
5. Vermischung alter und neuer Exporte
6. nicht atomare Schreibvorgänge
7. noch unzureichend getestete MSG- und PST-Importer
8. fehlende automatisierte Tests

## 3. Aktueller Funktionsumfang

### 3.1 Eingabeformate

- `.eml`
- `.msg` über `extract-msg`
- `.pst` über klassisches Outlook oder optional `libpff`/`pypff`

### 3.2 Ausgabeformate

- Parquet
- CSV
- Excel über die Kommandozeile
- JSON
- XML
- Markdown-Einzeldatei
- Markdown-Monatsordner mit `index.csv` und `index.jsonl`

### 3.3 GUI-Workflow

1. Systemcheck
2. Daten und Ausgabe festlegen
3. Dateivorprüfung
4. Verarbeitung mit Fortschrittsanzeige
5. Ergebnisanzeige mit vollständigem Zielpfad

### 3.4 Lokaler Betrieb

Der Hauptworkflow arbeitet lokal. Es werden keine Cloud-APIs oder externen Analysedienste aufgerufen. Python-Abhängigkeiten werden in der Entwicklungsphase installiert und in die portable EXE aufgenommen. Mulish wird als lokale Schriftressource gebündelt und nur für den laufenden Prozess registriert.

## 4. Kritische Befunde – Priorität P1

P1 bedeutet: vor einem echten Pilot mit großen Archiven beheben.

### P1.1 Verarbeitung ist nicht auf große Archive ausgelegt

PST-Nachrichten werden vollständig in Listen gesammelt. Anschließend werden alle Nachrichten gemeinsam in einen Pandas-DataFrame übernommen. Pro Nachricht werden unter anderem Rohtext, bereinigter Text und HTML gleichzeitig im Arbeitsspeicher gehalten.

Fundstellen:

- `mail_analyst.py:580`
- `mail_analyst.py:640`
- `mail_analyst.py:871`
- `mail_analyst_gui.py:545`

Risiken:

- sehr hoher RAM-Verbrauch
- mehrfacher Speicherbedarf durch ähnliche Body-Felder
- lange Blockierung beim Aufbau der Ergebnistabelle
- Absturz oder starke Verlangsamung bei großen PST-Dateien
- einzelne große JSON-Dateien werden unhandlich

Empfehlung:

- Nachrichten stapelweise beziehungsweise streamend verarbeiten
- Zwischenergebnisse direkt auf Datenträger schreiben
- JSONL und partitionierte Parquet-Dateien für große Datenmengen anbieten
- Ergebnistabelle auf eine begrenzte Vorschau reduzieren
- Gesamtzahlen getrennt von der Nachrichtenvorschau anzeigen

### P1.2 Cache liegt außerhalb des gewählten Zielordners

Die GUI verwendet derzeit den relativen Standardcache:

```text
.mailanalyst_cache/mail_metadata.pkl
```

Fundstellen:

- `mail_analyst.py:28`
- `mail_analyst_gui.py:511`

Der Cache enthält den vollständigen DataFrame und damit potentiell:

- Absender und Empfänger
- Betreffzeilen
- Rohtext
- bereinigten Text
- HTML-Inhalte
- Dateipfade

Damit können schützenswerte Maildaten außerhalb des vom Benutzer gewählten Zielordners verbleiben. Der tatsächliche Ablageort hängt zudem vom aktuellen Arbeitsverzeichnis ab.

Empfehlung:

- Cache standardmäßig in den gewählten Zielordner verschieben
- Cachepfad in GUI und Laufmanifest anzeigen
- optionalen Verzicht auf Cache ermöglichen
- Cache eindeutig dem Eingabebestand und dem Lauf zuordnen

### P1.3 Pickle-Cache ist ein Sicherheits- und Robustheitsrisiko

Der Cache wird mit `pd.read_pickle()` geladen.

Fundstelle:

- `mail_analyst.py:789`

Pickle ist kein sicheres Austauschformat. Ein manipulierter Cache kann beim Laden Python-Code ausführen. Ein beschädigter Cache bricht den Lauf derzeit außerdem ab, statt kontrolliert verworfen und neu aufgebaut zu werden.

Empfehlung:

- Pickle durch Parquet oder SQLite ersetzen
- Cacheversion und Schema explizit prüfen
- beschädigte Caches isolieren und neu aufbauen
- keine ausführbaren Serialisierungsformate für Maildaten verwenden

### P1.4 SHA-256 kann bei Cachetreffern veraltet sein

Standardmäßig wird ein Cachetreffer anhand von Dateigröße und Änderungszeit erkannt. Der im Cache gespeicherte SHA-256 wird nur bei aktivierter strenger Hashprüfung verglichen.

Fundstellen:

- `mail_analyst.py:796`
- `mail_analyst.py:842`
- `mail_analyst.py:844`

Dadurch kann der exportierte Hash aus einem früheren Lauf stammen und nicht mehr den aktuell vorliegenden Dateiinhalt repräsentieren. Für Nachweis- und Belegzwecke ist das kritisch.

Empfehlung:

- Hashprüfung für beweisorientierte Profile verpflichtend aktivieren
- alternativ Hash vor jedem Export neu verifizieren
- klar zwischen `source_hash_verified_at` und historischem Cachehash unterscheiden
- Verifikationszeitpunkt im Laufmanifest speichern

### P1.5 Mehrere GUI-Läufe können gleichzeitig schreiben

Der Verarbeitungsstart wird während eines laufenden Jobs nicht vollständig gesperrt. Optionen und Zielpfad können weiterhin verändert werden. Der Hintergrundthread greift zudem direkt auf Tkinter-Variablen zu.

Fundstellen:

- `mail_analyst_gui.py:491`
- `mail_analyst_gui.py:502`
- `mail_analyst_gui.py:525`

Risiken:

- parallele Schreibvorgänge in dieselben Dateien
- beschädigte Cache- oder Exportdateien
- uneindeutige Laufoptionen
- schwer reproduzierbare Fehler

Empfehlung:

- vor dem Start einen unveränderlichen Jobauftrag erzeugen
- alle GUI-Werte im Hauptthread in normale Python-Werte kopieren
- Startknöpfe und Navigation während des Jobs sperren
- genau einen aktiven Job zulassen
- kontrolliertes Abbrechen und Schließen implementieren

### P1.6 Alte und neue Ausgaben können vermischt werden

MailAnalyst schreibt wiederholt in denselben Zielordner. Dateien aus früheren Läufen, die im neuen Profil nicht erzeugt werden, bleiben erhalten. Auch nicht mehr benötigte Markdown-Monatsdateien werden nicht entfernt.

Fundstellen:

- `mail_analyst_gui.py:525`
- `mail_analyst.py:926`

Beispiel:

Ein Analysepaket erzeugt Parquet, JSON und Markdown. Ein späterer reiner JSON-Lauf überschreibt nur `emails.json`. Die alten Parquet- und Markdown-Dateien bleiben daneben liegen. Ein Coding Agent könnte dadurch veraltete Inhalte durchsuchen.

Empfehlung:

- pro Lauf einen eindeutigen Unterordner verwenden
- beispielsweise `2026-09-04_205500_<lauf-id>`
- Laufstatus `in_progress`, `complete` oder `failed` dokumentieren
- finalen Export erst nach erfolgreicher Validierung freigeben
- erzeugte Dateien in einem Manifest vollständig auflisten

### P1.7 CSV- und Excel-Formelinjektion

Mailfelder werden unverändert nach CSV und XLSX geschrieben. Beginnt ein Textfeld mit `=`, `+`, `-` oder `@`, kann Excel es als Formel interpretieren.

Fundstellen:

- `mail_analyst.py:881`
- `mail_analyst.py:883`

E-Mail-Inhalte müssen als nicht vertrauenswürdige Eingaben behandelt werden.

Empfehlung:

- potentiell gefährliche Zellanfänge für Sicht- und Reviewexporte neutralisieren
- Masterformate wie Parquet und JSON unverändert halten
- Schutzverhalten dokumentieren und testen

## 5. Wichtige Befunde – Priorität P2

P2 bedeutet: zeitnah beheben, bevor der Workflow breiter verteilt wird.

### P2.1 Outlook-PST-Lifecycle ist nicht vollständig robust

Eine PST wird immer über `AddStoreEx` hinzugefügt, auch wenn sie bereits in Outlook eingebunden ist. Frühe Fehler können außerdem auftreten, bevor der aktuelle `finally`-Block erreicht wird.

Fundstellen:

- `mail_analyst.py:570`
- `mail_analyst.py:573`
- `mail_analyst.py:604`

Empfehlung:

- bereits eingebundene Stores wiederverwenden
- COM-Initialisierung und Store-Cleanup in einen äußeren `try/finally`-Block legen
- nur von MailAnalyst selbst eingebundene Stores entfernen
- Fehler beim Entfernen protokollieren

### P2.2 Exchange-Adressen werden nicht zuverlässig als SMTP aufgelöst

Outlook-Eigenschaften wie `SenderEmailAddress`, `To` und `CC` können Anzeigenamen oder interne Exchange-Adressen enthalten. Für Beteiligten- und Kommunikationsanalysen werden jedoch stabile SMTP-Adressen benötigt.

Fundstellen:

- `mail_analyst.py:510`
- `mail_analyst.py:535`
- `mail_analyst.py:537`

Empfehlung:

- Absender über `Sender.GetExchangeUser()` beziehungsweise PropertyAccessor auflösen
- Empfänger über die Outlook-Recipients-Collection einzeln erfassen
- Anzeigename und SMTP-Adresse getrennt speichern
- nicht auflösbare Empfänger ausdrücklich kennzeichnen

### P2.3 MSG- und PST-Importer sind nicht praktisch verifiziert

Im aktuellen Testbestand liegen ausschließlich zehn EML-Dateien. Es gibt keine MSG- oder PST-Testfixtures. `pypff` ist in der aktuellen Umgebung nicht installiert.

Folge:

- EML ist praktisch verifiziert
- MSG ist nur aufgrund vorhandener Bibliothek plausibel
- Outlook-PST ist nicht mit einem Testarchiv verifiziert
- libpff-PST ist weder installiert noch verifiziert

Empfehlung:

- kleine synthetische MSG- und PST-Testarchive erstellen
- Ordner, Unterordner, HTML, Anlagen und fehlerhafte Nachrichten abdecken
- Bibliotheksversion für libpff festlegen
- beide PST-Wege gegen denselben Erwartungsdatensatz vergleichen

### P2.4 Vorprüfung und Verarbeitung sind nicht an denselben Dateistand gebunden

Die Vorprüfung speichert Größe und Änderungszeit. Vor der Verarbeitung wird aber nicht kontrolliert, ob sich die Datei seitdem verändert hat.

Fundstellen:

- `preflight.py:44`
- `mail_analyst_gui.py:491`

Empfehlung:

- Größe und `modified_at_ns` unmittelbar vor der Verarbeitung erneut vergleichen
- bei Abweichung Verarbeitung anhalten oder erneute Vorprüfung verlangen
- bei strengem Profil zusätzlich den Hash aus der Vorprüfung vergleichen

### P2.5 Status „Ignoriert“ wird bei Ordnerläufen praktisch nicht erreicht

`discover_mail_files()` filtert alle nicht unterstützten Erweiterungen bereits vor der Vorprüfung heraus. Dadurch können solche Dateien nicht als ignoriert in der Vorprüfung erscheinen.

Fundstellen:

- `mail_analyst.py:778`
- `preflight.py:76`

Empfehlung:

- Vorprüfung alle Dateien inventarisieren lassen
- anschließend unterstützte und ignorierte Dateien klassifizieren
- Anzahl ignorierter Dateien und Erweiterungen zusammenfassen

### P2.6 GUI-Protokollierung ist unvollständig

Der CLI-Workflow protokolliert Eingabe, Ausgabe, Optionen, Laufzeit und Ergebnis. Die GUI konfiguriert lediglich den Logger. Bei vollständigen Cachetreffern kann `parse_log.txt` leer bleiben.

Fundstellen:

- `mail_analyst_gui.py:505`
- `mail_analyst.py:1082`

Dieses Verhalten wurde bei einem GUI-Lauf beobachtet.

Empfehlung:

- gemeinsame Laufprotokollfunktion für CLI und GUI verwenden
- Lauf-ID, Start, Ende, Optionen und Ergebnis immer protokollieren
- Cachetreffer und echte Parserläufe getrennt zählen
- Ausgabedateien samt Größe und Hash protokollieren

### P2.7 Exporte werden nicht atomar geschrieben

JSON, Parquet, Markdown, Cache und Berichte werden direkt unter dem endgültigen Dateinamen geschrieben. Ein Absturz oder volles Laufwerk kann unvollständige Dateien hinterlassen.

Empfehlung:

- zuerst in einen temporären Laufordner schreiben
- jede Ausgabe nach dem Schreiben validieren
- danach atomar umbenennen
- unvollständige Läufe sichtbar als fehlgeschlagen markieren

### P2.8 Systemcheck prüft nicht den gewählten Zielort

Der Systemcheck prüft temporären Schreibzugriff und freien Speicherplatz des temporären Systemlaufwerks. Der spätere Zielordner kann jedoch auf einem anderen lokalen Laufwerk oder Fileserver liegen.

Fundstellen:

- `system_check.py:112`
- `system_check.py:122`

Empfehlung:

- nach Auswahl des Zielordners einen zweiten zielbezogenen Check ausführen
- Schreibtest, Umbenennen, Löschen, freien Speicherplatz und verfügbare Dateisystemfunktionen prüfen
- Netzwerkunterbrechung als eigenen Fehlerfall behandeln

### P2.9 Hintergrundthreads und Schließen der GUI

Systemcheck, Vorprüfung und Verarbeitung verwenden Daemon-Threads. Beim Schließen der GUI kann der Prozess beendet werden, während Dateien geschrieben werden.

Empfehlung:

- aktiven Jobstatus zentral verwalten
- beim Schließen warnen
- kontrolliertes Abbrechen oder Warten ermöglichen
- keine endgültigen Dateien direkt aus einem abbrechbaren Thread schreiben

### P2.10 Markdown kann durch Mailinhalte strukturell beeinflusst werden

Betreff und Body stammen aus nicht vertrauenswürdigen E-Mails. Markdown-Sonderzeichen und HTML können die Dokumentstruktur beeinflussen. Body-Überschriften werden nur teilweise maskiert.

Fundstellen:

- `mail_analyst.py:907`
- `mail_analyst.py:948`
- `mail_analyst.py:960`

Empfehlung:

- Metadatenfelder Markdown-sicher escapen
- rohen Mailtext klar von generierter Steuerstruktur trennen
- optional strukturierte Frontmatter- oder JSONL-Metadaten verwenden

## 6. Fachliche Lücken für Recherche in archivierter Kommunikation

Die folgenden Punkte sind keine unmittelbaren Defekte, aber für den späteren Einsatzzweck relevant:

- Deduplizierung über EML-, MSG- und PST-Quellen
- Konversations- und Threadzuordnung
- Erkennung von Versand- und Empfangsrichtung relativ zum Postfach
- Normalisierung von Beteiligten und E-Mail-Aliasen
- Hashes für Anlagen
- optionaler Anlagenexport
- Erkennung eingebetteter und fehlender Anlagen
- Verknüpfung von Antwortketten
- Erfassung von ReceivedTime zusätzlich zu SentOn
- stabile Projekt- und Laufkennungen
- Laufmanifest mit Softwareversion und Ausgabehashes
- Trennung von Originaldaten, normalisierten Daten und Analyseansichten

## 7. Sicherheitsmodell für spätere KI- oder Agentennutzung

E-Mail-Inhalte sind nicht vertrauenswürdig. Sie können Texte enthalten, die wie Anweisungen an einen Coding Agent oder ein Sprachmodell formuliert sind.

Vor einer Agentenanalyse sollte deshalb gelten:

- Mailtexte sind ausschließlich Daten und niemals Arbeitsanweisungen
- Agenten erhalten nur lesenden Zugriff auf den Exportbestand
- keine Befehle oder Links aus Mailinhalten ausführen
- keine externen URLs automatisch öffnen
- Originalarchive bleiben unverändert und außerhalb der Analyseumgebung
- Analyseergebnisse müssen auf Message-ID, Quellpfad und Hash zurückverweisen
- sensible Daten dürfen die geschützte Umgebung nicht verlassen

## 8. GUI-Review

### Positiv

- klare Fünf-Schritt-Navigation
- Systemcheck und Dateivorprüfung sind getrennt
- verständliche Freischaltung der Arbeitsschritte
- Oberflächengestaltung ist konsistent umgesetzt
- Mulish wird lokal geladen und geprüft
- Warnungen und Fehler sind visuell unterscheidbar
- Zielpfad wird am Ende vollständig angezeigt und kann kopiert werden
- Hintergrundverarbeitung hält die GUI bei kleinen Läufen grundsätzlich bedienbar
- Ausgabeordner und Log können direkt geöffnet werden

### Verbesserungsbedarf

- Verarbeitung kann nicht kontrolliert abgebrochen werden
- kein Schutz gegen Mehrfachstart
- Optionen bleiben während der Verarbeitung veränderbar
- kein Fortschritt für die eigentliche Exportphase
- keine Anzeige der erzeugten Einzeldateien
- keine Anzeige von Ausgabegrößen und Ausgabehashes
- Ergebnistabelle ist nicht für große Datenmengen virtualisiert
- kein Hinweis beim Schließen während eines laufenden Jobs
- keine Laufzeitschätzung
- keine klare Darstellung von Cachetreffern gegenüber neu geparsten Quellen
- fehlende profilabhängige Blockierung nicht verfügbarer Backends

## 9. Systemcheck-Review

### Positiv

- startet automatisch
- zeigt Laufzeit, Pakete, Importer und Ressourcen
- unterscheidet Fehler und optionale Warnungen
- prüft, ob Mulish tatsächlich aktiv ist
- dokumentiert Ergebnisse als CSV und JSON
- verhindert bei Kernfehlern den nächsten Schritt

### Verbesserungsbedarf

- `find_spec()` bestätigt nur Auffindbarkeit, nicht zwingend einen erfolgreichen Funktionsimport
- Outlook wird über Registrierung, aber nicht durch einen kontrollierten COM-Selbsttest geprüft
- Prüfung ist noch nicht vom gewählten Eingabeformat und Ausgabeprofil abhängig
- Zielordner wird erst später gewählt und deshalb nicht geprüft
- keine Schätzung des benötigten Speicherplatzes anhand der Eingabemenge

## 10. Vorprüfungs-Review

### Positiv

- leere Dateien werden erkannt
- EML-Header und grundlegende MIME-Auffälligkeiten werden geprüft
- MSG-/OLE- und PST-Signaturen werden plausibilisiert
- Lesefehler werden pro Datei dokumentiert
- Warnungen können ein- oder ausgeschlossen werden
- problematische Einzelquellen können bewusst ausgewählt werden
- CSV- und JSON-Berichte werden erzeugt

### Verbesserungsbedarf

- Signaturprüfung bestätigt keine vollständige strukturelle Lesbarkeit
- große EML-Header oberhalb des Prüfbereichs werden nicht vollständig berücksichtigt
- ignorierte Dateitypen werden bei Ordnerläufen vorher ausgefiltert
- Dateistand wird vor der Verarbeitung nicht erneut abgeglichen
- keine Pfadlängen-, Namens- oder Netzlaufwerksprüfung
- keine Prüfung auf Passwortschutz oder Verschlüsselung von PST-Dateien

## 11. Parser- und Datenmodellreview

### Positiv

- gemeinsames Schema für unterschiedliche Eingabeformate
- Parserfehler werden nicht still verworfen
- Quellpfad und Datei-SHA-256 werden grundsätzlich erfasst
- Message-ID, In-Reply-To und References werden bei EML berücksichtigt
- Rohtext, bereinigter Text und HTML bleiben erhalten
- deutsche Datumsfelder sind praktisch für Auswertung und Filter
- Anlagenamen und Anlagenanzahl werden inventarisiert
- HTML wird ohne Browser und ohne Abruf externer Ressourcen verarbeitet
- Parserfehler einzelner grundsätzlich lesbarer Dateien werden als Datenzeile ausgegeben

### Verbesserungsbedarf

- Datenmodell hat keine explizite Schemadefinition
- keine Validierung verpflichtender Felder
- keine eindeutige interne Nachrichten-ID über alle Formate
- keine Deduplizierungsstrategie
- interne Exchange-Adressen werden nicht vollständig normalisiert
- naive Datumswerte werden pauschal als UTC interpretiert
- Anhänge werden nicht gehasht
- eingebettete Nachrichten und Sonderobjekte sind nicht ausreichend spezifiziert
- vollständiger HTML-Body vergrößert Cache und Exporte erheblich

## 12. Exportreview

### Positiv

- alle vorgesehenen Formate werden grundsätzlich erzeugt
- JSON verwendet UTF-8 und erhält Unicode
- CSV verwendet UTF-8 mit BOM für bessere Excel-Kompatibilität
- Excel-Zelllängen werden begrenzt
- XML entfernt unzulässige Steuerzeichen
- Markdown kann nach Monaten partitioniert werden
- Markdown-Suchindex enthält wichtige Metadaten
- Linkdarstellung kann für Markdown gewählt werden
- Parquet und JSON bleiben als Masterdaten von der Markdown-Linkreduktion unberührt

### Verbesserungsbedarf

- keine atomaren Schreibvorgänge
- keine abschließende Formatvalidierung im normalen Workflow
- keine Ausgabehashes
- keine eindeutige Run-ID
- keine Bereinigung veralteter Monatsdateien
- große JSON-Arrays sind schlecht streambar
- CSV und Excel benötigen Schutz gegen Formelinjektion
- Markdown benötigt robustere Maskierung und optionale Signatur-/Footerbereinigung
- `mailto:` und `tel:` werden im Linkmodus nicht überall einheitlich behandelt
- unmittelbar doppelte Textzeilen aus HTML-Layouts bleiben teilweise erhalten

## 13. Build- und Abhängigkeitsreview

### Aktueller Build

- PyInstaller `onedir`
- portable EXE ohne separate Python-Installation
- Mulish-Schriften und Lizenz werden gebündelt
- `extract-msg`, `pyarrow` und `pywin32` werden aufgenommen
- `pypff` ist nicht enthalten

### Beobachtete Größe

- etwa 2.582 Dateien
- etwa 166 MB Gesamtgröße
- etwa 14 MB Haupt-EXE

### Risiken und Verbesserungen

- `--collect-all pyarrow` nimmt unnötige Testmodule auf
- Build erzeugt zahlreiche Warnungen aus optionalen Testabhängigkeiten
- Abhängigkeiten sind nur durch Mindestversionen begrenzt
- Builds sind dadurch nicht vollständig reproduzierbar
- keine Anwendungsversionsnummer
- kein Buildmanifest
- keine veröffentlichte SHA-256-Prüfsumme
- keine Codesignatur
- kein automatisierter Buildtest

Empfehlung:

- geprüfte Versionen in einer Lockdatei festhalten
- nur benötigte PyArrow-Komponenten bündeln
- Versionsnummer und Builddatum integrieren
- SHA-256 für das Distributionspaket erzeugen
- optional interne Codesignatur für verteilte EXE verwenden

## 14. Dokumentationsreview

### Positiv

- Setup und CLI-Aufrufe sind beschrieben
- GUI-Workflow ist erklärt
- lokale Arbeitsweise wird deutlich gemacht
- Ausgabeformate und Cacheoptionen sind dokumentiert
- Schriftlizenz wird erwähnt

### Veraltete oder unvollständige Stellen

- die anfängliche Dateiliste im README enthält nicht alle neuen Module
- die Ergebnistabelle wird teilweise mit nicht vorhandenen Spalten beschrieben
- eine alte Beschreibung des früheren Prüfablaufs ist noch enthalten
- `.github/copilot-instructions.md` behauptet noch, PST benötige grundsätzlich Outlook
- neue Systemcheck- und Vorprüfmodule fehlen in der Projektübersicht
- Sicherheitsregeln für untrusted Mailcontent fehlen
- Verhalten bei Wiederverwendung eines Zielordners ist nicht dokumentiert

## 15. Test- und Qualitätsstand

### Erfolgreich verifiziert

- Syntaxprüfung aller Python-Module
- `pip check` ohne defekte Abhängigkeiten
- zehn EML-Dateien verarbeitet
- zehn von zehn EML-Datensätzen mit Parserstatus `ok`
- JSON mit Python und PowerShell validiert
- CSV erzeugt
- Parquet erzeugt
- XML erzeugt
- Markdown-Einzeldatei erzeugt
- drei Markdown-Monatschunks erzeugt
- Markdown-Index erzeugt
- Mulish in der Entwicklungsumgebung lokal geladen
- Systemcheck ausgeführt
- portable EXE mehrfach erfolgreich gebaut

### Nicht verifiziert

- reale MSG-Dateien
- reale PST über klassisches Outlook
- reale PST über `libpff`
- mehrere PST-Dateien in einem Lauf
- PST, die bereits in Outlook eingebunden ist
- beschädigte oder passwortgeschützte PST
- hunderttausende oder Millionen Nachrichten
- Netzwerkpfade und Fileserverunterbrechungen
- volles Laufwerk während des Exports
- Abbruch und Neustart eines Laufs
- beschädigter Cache
- paralleler GUI-Start
- Formel- und Markdown-Injektion

### Fehlende Testinfrastruktur

- keine Unit-Tests
- keine Integrationstests
- keine Regressionstests
- keine Testfixtures für MSG und PST
- keine CI-Konfiguration
- keine Performance- oder Speichertests

## 16. Repository-Zustand

Zum Reviewzeitpunkt war ein großer Teil der aktuellen Entwicklung noch nicht committed.

Geändert oder neu waren unter anderem:

- `mail_analyst.py`
- `mail_analyst_gui.py`
- `preflight.py`
- `system_check.py`
- `build_exe.ps1`
- `requirements.txt`
- `requirements-dev.txt`
- `README.md`
- `.gitignore`
- `.github/copilot-instructions.md`
- `assets/fonts/`

Vor der nächsten größeren Änderung sollte der aktuelle funktionierende Stand in einem nachvollziehbaren Commit gesichert werden.

## 17. Empfohlene Umsetzungsreihenfolge

### Phase 1 – Integrität und sichere Laufstruktur

1. Cache in den Zielordner verlegen.
2. Pickle durch Parquet oder SQLite ersetzen.
3. Hashprüfung und Cacheintegrität überarbeiten.
4. Pro Lauf einen eindeutigen Ausgabeordner erzeugen.
5. Laufmanifest mit Run-ID, Optionen, Versionen und Hashes einführen.
6. Exporte atomar schreiben und anschließend validieren.

### Phase 2 – GUI und Jobsteuerung härten

1. Unveränderlichen Jobauftrag beim Start erzeugen.
2. Mehrfachstart verhindern.
3. Eingaben und Navigation während des Laufs sperren.
4. Schließen während laufender Verarbeitung behandeln.
5. kontrolliertes Abbrechen ermöglichen.
6. Ergebnisansicht auf Vorschau begrenzen.
7. erzeugte Dateien, Größen und Hashes anzeigen.

### Phase 3 – Skalierung

1. Parser und Exporte in Batches umstellen.
2. PST-Nachrichten nicht vollständig im RAM sammeln.
3. partitioniertes Parquet einführen.
4. JSONL als Großdatenformat ergänzen.
5. Speicher- und Performancetests entwickeln.
6. Wiederaufnahme unterbrochener Läufe ermöglichen.

### Phase 4 – Testabdeckung und PST-Qualität

1. Pytest-Grundstruktur einführen.
2. synthetische EML-, MSG- und PST-Fixtures erstellen.
3. Outlook-Store-Lifecycle testen und härten.
4. libpff-Backend real testen.
5. Exchange-SMTP-Auflösung implementieren.
6. Cachemigrationen und defekte Dateien testen.

### Phase 5 – Fachliche Aufbereitung

1. Deduplizierung entwickeln.
2. Thread- und Konversationsbeziehungen ableiten.
3. Nachrichtenrichtung bestimmen.
4. Beteiligte und Alias-Adressen normalisieren.
5. Anlagen hashen und optional exportieren.
6. Signaturen, Footer und zitierte Historien als optionale Transformationsstufen anbieten.

### Phase 6 – Vorbereitung auf lokale KI-Analyse

1. unveränderliche Rohdaten und Analyseansichten trennen.
2. agentenfreundlichen Index definieren.
3. Prompt-Injection-Schutzregeln dokumentieren.
4. lokale, rein lesende Analyseumgebung vorsehen.
5. jede KI-Aussage auf konkrete Nachrichten und Quellen zurückführbar machen.

## 18. Empfohlener Einstieg für die nächste Sitzung

Die nächste Sitzung sollte mit Phase 1 beginnen. Der sinnvollste erste Arbeitsblock ist:

1. Laufordner- und Manifestkonzept festlegen.
2. Cachepfad aus dem Arbeitsverzeichnis in den Zielbereich verschieben.
3. Pickle-Cache durch ein nicht ausführbares Format ersetzen.
4. Cachehash und Quelldateihash eindeutig definieren.
5. Tests für Cachetreffer, geänderte Dateien und beschädigte Caches ergänzen.

Erst danach sollten größere echte Projektarchive verarbeitet werden.

## 19. Kurzfazit

MailAnalyst erfüllt bereits den Zweck eines lokalen EML-Prototyps und besitzt eine brauchbare Benutzerführung. Der Kernworkflow ist nachvollziehbar, die Exportformate funktionieren und die Anwendung bleibt zur Laufzeit unabhängig von Cloud-Diensten.

Die nächste Entwicklungsphase sollte nicht mit zusätzlichen KI-Funktionen beginnen, sondern mit Integrität, Cachehärtung, Laufisolation, Skalierung und automatisierten Tests. Diese Maßnahmen schaffen die Grundlage dafür, dass spätere Analysen von Aktivitäten und Themenverläufen belastbar und reproduzierbar sind.
