# MailAnalyst 0.5.0-dev.1

Entwicklungskandidat, keine Freigabe fuer Echtdaten oder produktiven Betrieb.

- Zentrale App-Version in Fenstertitel, CLI und Laufmanifest.
- Portable Builds mit Quellrevision, Kennzeichnung lokaler Aenderungen,
  Quellbaum-Hash, Python-/Paketversionen und Paketpruefsummen.
- Vollstaendige GUI-Dateiinventarisierung einschliesslich ignorierter Dateien.
- Ausgewaehlte Quellen werden beim Import gegen die SHA-256-Vorpruefung gebunden.
- Auftragsbezogene Komponenten- und Schreib-/Speicherpruefung in GUI und CLI.

Bekannte Grenzen: Kein abgenommener echter PST-Importweg, keine Wiederaufnahme
nach Prozessabbruch, keine Gesamt-RAM-/Laufzeitgarantie. Die Platzabschaetzung ist
eine Warnschwelle und keine Garantie. Outlook-Registrierung beweist keine
erreichbare COM-Sitzung. Originalschutz ohne unveraenderlichen Quellsnapshot
bleibt begrenzt. Vollstaendige Abnahmekriterien: docs/01_guides/ROADMAP.md.
