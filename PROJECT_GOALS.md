# MailAnalyst – Projektziele

Stand: 5. September 2026

## 1. Zweck und Verbindlichkeit

Dieses Dokument beschreibt die funktionalen Ziele und Rahmenbedingungen der Anwendung.

Die Abschnitte 2 bis 6 beschreiben den vorgesehenen Funktionsumfang. Die Erfolgskriterien in Abschnitt 7 sind daraus abgeleitete Vorschläge; konkrete Mengen- und Leistungsziele sind noch offen. Technische Empfehlungen aus dem Review sind in Abschnitt 8 gesondert aufgeführt und damit nicht automatisch verbindliche Produktanforderungen.

Dieses Dokument beschreibt den angestrebten Nutzen und Umfang. Die [README](README.md) erklärt die Bedienung; der [Reviewbericht](REVIEW_REPORT.md) dokumentiert technische Befunde, Testgrenzen und Umsetzungsempfehlungen. Ein dokumentiertes Ziel bedeutet nicht, dass es bereits umgesetzt oder verifiziert ist.

## 2. Übergeordnetes Ziel

MailAnalyst soll große, über mehrere Jahre gewachsene E-Mail-Bestände aus umfangreichen Archiven lokal einlesen, Daten daraus extrahieren und für Suche und spätere KI-Auswertungen strukturiert bereitstellen.

Die Anwendung unterstützt die langfristige Erschließung archivierter Kommunikation und ihrer Themenverläufe.

Anwender können relevante Nachrichten finden, zeitlich einordnen und mit ihren Quellenbezügen zusammenstellen.

## 3. Anwender und Anwendungsfälle

### Anwender

- Der Projektverantwortliche bereitet Mailarchive auf und erprobt die weitere Analyse.
- Kollegen recherchieren darin projektbezogene Informationen und Belege.
- Später können lokale LLMs oder Coding Agents die aufbereiteten Bestände in einer geschützten Analyseumgebung durchsuchen.

### Zentrale Anwendungsfälle

1. Herkömmliche Outlook-Mails von einem Fileserver oder aus einem wiederhergestellten PST-Archiv gesammelt einlesen und transformieren.
2. Kommunikation zu einem Thema über mehrere Jahre auffinden und ihren zeitlichen Verlauf nachvollziehen.
3. Aktivitäten und relevante Informationen nach Zeitraum, Thema, Absender oder Empfänger recherchieren.
4. E-Mails als Informationsgrundlage für Recherchen und nachvollziehbare Quellenbelege zusammenstellen.
5. Einen eigenständigen Ausgabeordner in eine Entwicklungsumgebung oder andere isolierte Umgebung übertragen und dort weiter durchsuchen.

Die Beispiele beschreiben Rechercheziele. Eine automatische fachliche Bewertung oder Erstellung fachlicher Bewertungen ist bisher nicht als Anforderung festgelegt.

## 4. Umfang der ersten Ausbaustufe

### Import und Datenaufbereitung

- EML-, MSG- und PST-Quellen unterstützen.
- Einzeldateien und Ordnerbestände stapelweise verarbeiten können.
- Für PST sowohl einen Weg über klassisches Outlook als auch einen unabhängigen Importweg vorsehen; den Verarbeitungsweg auswählbar machen.
- Mailinhalte und Metadaten in strukturierte und gut lesbare Ausgabeformate überführen.
- Große, mehrjährige Bestände als Zielgröße berücksichtigen; eine konkrete Nachrichtenanzahl oder Archivgröße ist noch nicht vereinbart.

### Ausgaben und spätere Suche

- Den Nutzer vor der Verarbeitung Ausgabeformat beziehungsweise Ausgabeprofil auswählen lassen.
- Parquet, CSV, JSON, XML und Markdown für unterschiedliche Auswertungs- und Recherchewege bereitstellen.
- Markdown nach Monaten aufteilen und über einen Index nach Zeitraum und Metadaten erschließbar machen.
- Die Darstellung von Links vorab auswählbar machen, da vollständige URLs je nach Recherche hilfreich oder störend sein können.
- Sämtliche für die Weiterverwendung benötigten Ausgaben in einem vom Nutzer gewählten separaten Zielordner bereitstellen.
- Die Aufbereitung so gestalten, dass zunächst auch editor- oder dateibasierte Recherche möglich ist.

### Bedienung und Bereitstellung

- Eine einfache Desktop-GUI anbieten, die ohne komplexes UI-Framework auskommt.
- Einen geführten Ablauf bereitstellen: Systemcheck, Eingabe und Ausgabe festlegen, Dateivorprüfung, Ergebnisse sichten und Quellen auswählen, Verarbeitung mit Fortschrittsanzeige, Ergebnis und Log.
- Ungültige Dateien und Fragmente vor der eigentlichen Verarbeitung möglichst erkennen; Warnungen und Fehler verständlich darstellen.
- Am Ende den tatsächlichen Ausgabeort vollständig anzeigen.
- Die Anwendung als Windows-EXE starten können, ohne auf dem Zielrechner eine separate Python-Entwicklungsumgebung einzurichten.
- Eine moderne, übersichtliche Navigation bieten; Animationen sind nicht erforderlich.
- Eine konsistente Oberfläche verwenden: Mulish sowie `#414343`, `#D63C24`, `#EF7D00` und `#0090B6`. Die Schrift soll lokal verfügbar sein.

## 5. Betrieb und Schutz der Daten

Der Hauptworkflow soll lokal und eigenständig in einer geschützten Umgebung ausführbar sein. Für Import, Aufbereitung und Export sollen keine Cloud-Dienste oder externen APIs erforderlich sein. Hintergrund ist die mögliche Schutzbedürftigkeit der archivierten Nachrichten.

Python-Bibliotheken dürfen in der Entwicklungsumgebung heruntergeladen und installiert werden. Die Forderung nach lokalem Betrieb schließt solche Entwicklungsabhängigkeiten nicht aus. Benötigte Laufzeitkomponenten sollen bei der Bereitstellung berücksichtigt und vom Systemcheck kenntlich gemacht werden.

Eine eigene Verschlüsselungsfunktion ist ausdrücklich nicht erforderlich, da die Verarbeitung in bereits geschützten Umgebungen stattfindet.

Für spätere KI-Recherche ist der Transfer des Ausgabeordners in eine separate, isolierte Umgebung mit lokalen LLMs vorgesehen. Die früher erwähnten Tests mit Coding-Assistenten begründen keine Pflicht zu einer Cloud-Anbindung oder Freigabe sensibler Daten für externe Dienste.

## 6. Abgrenzungen und spätere Ausbaustufen

### Aktuell nicht vorgesehen

- Outlook-Mac-Archive.
- Analyse von Outlook-Vorlagen.
- Eine eigene Verschlüsselungslösung.
- Aufwendige Animationen oder ein komplexes Frontend-Framework.

### Erst später zu betrachten

- Datenbankanbindungen.
- Direkt integrierte KI-Funktionen.
- Weitergehende automatisierte fachliche Auswertungen.

Die erste Ausbaustufe soll zunächst den Import, die Transformation, die Exporte und eine brauchbare Benutzerführung liefern. Eine Datenbankanbindung als Produktfunktion ist dabei von der noch offenen technischen Wahl eines internen Cacheformats zu unterscheiden.

## 7. Vorgeschlagene Erfolgskriterien

Diese Kriterien konkretisieren die Ziele für spätere Abnahmen. Sie sind noch nicht als vollständig erreicht zu verstehen.

| Ziel | Vorschlag für einen überprüfbaren Nachweis |
| --- | --- |
| Relevante Quellen verarbeiten | Repräsentative EML-, MSG- und PST-Bestände werden mit erwarteten Nachrichten und Metadaten importiert; Fehler werden sichtbar ausgewiesen. |
| Lokal arbeiten | Import, Aufbereitung und Export funktionieren in der vorgesehenen Zielumgebung ohne Internetverbindung und ohne Cloud-API. |
| Einfache Bedienung | Ein Anwender kann Quelle, Importweg, Ausgabeprofil und Zielordner wählen und den geführten Ablauf bis zum Ergebnis abschließen. |
| Übertragbare Ergebnisse | Der Ausgabeordner lässt sich in eine separate Umgebung kopieren; Dateien und Indexverweise bleiben dort nutzbar. |
| Recherche ermöglichen | An einem Beispieldatensatz lassen sich Nachrichten nach Zeitraum, Thema, Absender und Empfänger auffinden. |
| Belege nachvollziehen | Ein Recherchefund lässt sich der ursprünglichen Nachricht beziehungsweise Quelle zuordnen. Die technischen Nachweisanforderungen sind noch zu konkretisieren. |
| Große Bestände bewältigen | Ein gemeinsam festgelegtes Testarchiv wird innerhalb noch zu bestimmender Laufzeit- und Speichergrenzen verarbeitet. |
| Portable Bereitstellung | Die ausgelieferte Windows-Anwendung startet auf einem repräsentativen Zielgerät; benötigte und fehlende Importkomponenten werden verständlich angezeigt. |

## 8. Technische Empfehlungen aus dem Review

Der Review vom 4. September bewertet den bestehenden Stand als funktionierenden EML-Prototyp. Reale MSG-/PST-Archive und große Datenmengen waren zu diesem Zeitpunkt noch nicht praktisch verifiziert.

Für einen belastbaren Pilot mit großen Archiven empfiehlt der Review insbesondere:

- Cache im Zielbereich ablegen und das ausführbare Pickle-Format ersetzen.
- Quelldateihashes zuverlässig prüfen und Herkunftsbezüge erhalten.
- Getrennte Laufordner, Laufmanifest und validierte, atomar geschriebene Exporte einführen.
- Konkurrierende GUI-Läufe verhindern und Abbruch beziehungsweise Schließen kontrollieren.
- Große Archive stapelweise verarbeiten und die GUI-Ergebnisvorschau begrenzen.
- Automatisierte Tests und repräsentative MSG-/PST-Testbestände ergänzen.
- Mailinhalte bei späterer Agentennutzung als Daten behandeln; Rechercheergebnisse auf Quellen zurückführen.

Diese Maßnahmen unterstützen die Projektziele. Die konkrete technische Umsetzung und Priorisierung sind im [Reviewbericht, Abschnitte 17 und 18](REVIEW_REPORT.md#17-empfohlene-umsetzungsreihenfolge) beschrieben. Der dort vorgeschlagene Einstieg ist Integrität und sichere Laufstruktur.

## 9. Noch offene Festlegungen

- Typische und maximale Archivgröße, Nachrichtenanzahl und Anzahl der Quellen pro Lauf.
- Zielhardware, erlaubte Laufzeit und verfügbarer Arbeitsspeicher.
- Ob der PST-Import ohne Outlook im ersten verteilten Paket zwingend enthalten sein muss.
- Welche Anlageninhalte später benötigt werden: nur Inventar, auch Export, Volltextsuche oder weitere Verarbeitung.
- Welche konkreten Recherchefragen und erwarteten Treffer als fachliche Abnahme dienen.
- Welche Anforderungen an die Dokumentation von Belegen und die Reproduzierbarkeit verbindlich gelten sollen.
- Welche spätere Analyseumgebung verwendet wird und wo die Grenze zwischen MailAnalyst und dieser Umgebung verläuft.

Diese Punkte sind bewusst offen; sie wurden nicht durch Annahmen oder Empfehlungen als bereits vereinbart festgeschrieben.
