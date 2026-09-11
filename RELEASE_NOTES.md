# MailAnalyst 0.7.0-dev.1

Entwicklungskandidat, keine Freigabe fuer Echtdaten oder produktiven Betrieb.

- Zentrale App-Version in Fenstertitel, CLI und Laufmanifest.
- Portable Builds mit Quellrevision, Kennzeichnung lokaler Aenderungen,
  Quellbaum-Hash, Python-/Paketversionen und Paketpruefsummen.
- Vollstaendige GUI-Dateiinventarisierung einschliesslich ignorierter Dateien.
- Ausgewaehlte Quellen werden beim Import gegen die SHA-256-Vorpruefung gebunden.
- Auftragsbezogene Komponenten- und Schreib-/Speicherpruefung in GUI und CLI.
- PST-Import ohne Outlook ueber das mitgelieferte `libpff-python-windows 20231205`.
  Die LGPLv3+-Lizenztexte liegen unter `_internal/licenses/libpff/`.
- libpff-PST-Dateien werden ueber einen eigenen binaeren Lesestrom geoeffnet,
  sodass der Windows-Build nicht vom Prozessarbeitsverzeichnis abhaengt.

Bekannte Grenzen: Der libpff-PST-Weg besitzt bisher nur eine kleine oeffentliche
Referenzdateipruefung; ein selbst erzeugtes PST-Sollarchiv sowie Offline- und
Zielsystemabnahme sind offen. Der vollstaendig bediente lokale EXE-PST-Erst- und
Cachelauf sind bestanden. Outlook ist nicht Teil der Pilotfreigabe.
Keine Wiederaufnahme
nach Prozessabbruch, keine Gesamt-RAM-/Laufzeitgarantie. Die Platzabschaetzung ist
eine Warnschwelle und keine Garantie. Outlook-Registrierung beweist keine
erreichbare COM-Sitzung. Originalschutz ohne unveraenderlichen Quellsnapshot
bleibt begrenzt. Vollstaendige Abnahmekriterien: docs/01_guides/ROADMAP.md.
