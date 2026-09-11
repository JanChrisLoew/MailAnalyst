# MailAnalyst – Versions- und Ausbauplanung

Stand: 11. September 2026. Planung auf Basis des [aktuellen Status](../STATUS.md).

Umsetzung fortgesetzt: `0.7.0-dev.1` ergänzt den versionierten Nachrichtenvertrag,
strukturierte Qualitätswarnungen, gehärtete Textausgaben und erste reale
PST-/MSG-Sonderformatnachweise. Ein optionaler
libpff-Integrationstest liest zusätzlich eine gültige öffentliche PST-Datei,
ohne sie zu verändern. Dies ist noch keine vollständige 0.7.0-Importabnahme.
Tatsächliche Nachweise und Restarbeiten stehen im Status.

## Ziel und Verbindlichkeit

Der Nutzer möchte erst mit Echtdaten in die geschützte Dev-Umgebung wechseln,
wenn die Anwendung hinreichend produktionsnah ist. Bis zu dieser Schwelle werden
Entwicklung und Abnahme ausschließlich mit synthetischen Inhalten durchgeführt.
Auch gültige MSG- und PST-Dateien dürfen ausschließlich erfundene Inhalte enthalten.

Die folgenden Versionen und Abnahmekriterien sind der konkrete Planungsvorschlag,
keine bereits veröffentlichten Releases oder erledigten Anforderungen. Dieser
Auftrag erstellt die Planung; er startet weder die Implementierung aller Pakete
noch einen Umzug, Commit, Push oder eine Echtdatenverarbeitung. Den tatsächlichen
Erledigungsstand führt ausschließlich STATUS; dieses Dokument führt Umfang und
Abhängigkeiten der geplanten Versionen. Offene Produktentscheidungen bleiben offen.

Die Umzugsschwelle ist **0.9.0-rc.1 mit bestandener synthetischer Gesamtabnahme**.
**1.0.0** folgt erst nach der kontrollierten Praxisabnahme in der Dev-Umgebung.
Synthetische Tests können hohe technische Reife belegen, aber die Besonderheiten
historischer Archive nicht vollständig vorwegnehmen.

## Ausgangspunkt

Nachgewiesen sind der 83-Test-Stand von 0.6.0-dev.1, ein gemischter Lauf mit 550
tatsächlichen MSG-/EML-Dateien und frühere synthetische EML-Großläufe. Eine
gültige öffentliche PST-Referenzdatei wurde inzwischen über den tatsächlichen
libpff-Dateipfad einschließlich Cache und Quellhash geprüft. Da ihr Inhalt nicht
vom Projekt selbst erzeugt wurde, ersetzt sie weder das geforderte synthetische
Sollarchiv noch die Outlook-Abnahme. Die jüngsten Arbeitsblöcke sind lokal und
nicht eingecheckt.

## Versionsfolge

| Version | Ergebnis | Voraussetzung für Abschluss |
| --- | --- | --- |
| 0.5.0 | Reproduzierbarer Ausgangsstand | Version, Quellstand, Abhängigkeiten und Build sind eindeutig zuordenbar. |
| 0.6.0 | Verlässliche Vorprüfung und Datenqualität | Quellenbilanz, Schema und Exporte bestehen definierte Fehler- und Inhaltstests. |
| 0.7.0 | Abgenommene Importwege | Jeder für den Pilot angebotene Importweg wurde mit gültigen synthetischen Dateien geprüft. |
| 0.8.0 | Robuster Betrieb großer Läufe | Abbruch, Absturz, Wiederaufnahme und Ressourcenfehler sind nachvollziehbar beherrscht. |
| 0.9.0-rc.1 | Kandidat für den Umzug | Alle Umzugskriterien bestanden; vollständiger EXE-Lauf auf sauberem Windows-Testsystem. |
| 0.9.0-rc.2 ff. | Korrekturen aus dem Dev-Pilot | Echtdatenbefunde behoben und soweit möglich synthetisch reproduziert. |
| 1.0.0 | Freigabe für den vereinbarten Betrieb | Fachliche Praxisabnahme und dokumentierte Betriebsgrenzen bestanden. |
| 1.1.0 / 1.2.0 | Optionale Rechercheerweiterungen | Gesonderte fachliche Priorisierung nach Stabilisierung des Kernworkflows. |

Keine Kalenderversprechen vor Klärung von PST-Weg, Zielhardware und Archivgröße.
Ein Meilenstein wird anhand seines Nachweises abgeschlossen, nicht anhand einer
bestimmten Testanzahl. Korrekturversionen wie 0.6.1 beheben Fehler im jeweiligen
Umfang. Änderungen am Datenformat benötigen eigene Kompatibilitätsregeln;
App-Version, Parserrevision und Cache-/Exportschema bleiben getrennte Angaben.

## 0.5.0 – Ausgangsstand und Releasegrundlage

Zugeordnete Aufgaben: REL-01, REPO-04, REPO-05.

1. Aktuellen Diff prüfen, bestehende Arbeitsblöcke nachvollziehbar zusammenstellen
   und einen lokalen Baseline-Nachweis erstellen. Commit/Tag nur im entsprechenden Auftrag.
2. Eine zentrale App-Version einführen; in GUI, CLI-Versionsausgabe und Manifest
   ausgeben. Buildmetadaten nennen Quellrevision und einen gegebenenfalls veränderten Stand.
3. Getestete Python- und Abhängigkeitsversionen für Windows festhalten und einen
   reproduzierbaren Installations-/Buildweg einführen. Die lokale Windows-Abnahme
   verwendet Python 3.11.9 und die Windows-Lockdatei.
4. Releasepaket mit Versionshinweisen, bekannten Grenzen und Prüfsummen vorsehen;
   Buildnachweis und Dokumentations-Linkprüfung lokal ausführen.
   GitHub-CI ist auf Nutzerwunsch vom 10. September 2026 nicht vorgesehen.

Abnahme: Ein frischer Checkout des festgelegten Quellstands lässt sich nach Anleitung
installieren, testen und bauen. Zwei Builds müssen dieselbe App-/Abhängigkeitsbasis
haben; byteidentische EXEs werden damit nicht automatisch zugesichert.

## 0.6.0 – Vorprüfung, Datenvertrag und Exportqualität

Zugeordnete Aufgaben: CHECK-01..03, DATA-07, EXPORT-01.

Umsetzungsstand vom 11. September: CHECK-01/02 und DATA-07/EXPORT-01 sind
implementiert und automatisiert geprüft. CHECK-03 bleibt wegen heuristischer
Platzabschätzung und nicht praktisch geprüfter Outlook-Bereitschaft teilweise.

1. Alle gefundenen Dateien inventarisieren. Auch ignorierte Dateien erscheinen im
   Bericht. Gefunden = unterstützt + ignoriert; unterstützt = ausgewählt + abgewählt.
   Quellenzahlen und Nachrichtenzahlen bleiben insbesondere bei PST getrennt.
2. Vorprüfung und Verarbeitung an denselben überprüften Quellenstand binden;
   geänderte Dateien benötigen eine erneute Vorprüfung. Berichte dem Lauf zuordnen.
3. Gewählte Ausgabe-/Arbeits-/Cachepfade und benötigte Importkomponenten prüfen.
   Platzbedarf abschätzen und Platzmangel während des Schreibens kontrolliert behandeln.
4. Versionierte Nachrichtenvalidierung ergänzen: Pflichtbezüge, Feldtypen,
   Datumsannahmen und strukturierte Qualitätswarnungen. Fehlende SMTP-Adressen
   dürfen nicht durch scheinbar gültige Anzeigenamen ersetzt werden.
5. Markdown-Metadaten und Mailtext robust von generierter Struktur trennen.
   XML-Zeichenverluste prüfen; verbleibende Formatverluste ausdrücklich ausweisen.
6. JSON/Parquet inhaltlich gegen feste Sollwerte prüfen; Sichtformate gegen ihre
   jeweils dokumentierte Semantik einschließlich Kürzungen und Formelpräfixen.

Abnahme: Synthetische Mischordner sind vollständig bilanziert. Geänderte Quellen,
fehlende Rechte, fehlende Komponenten und voller Zielbereich erzeugen verständliche
Fehler. Kein unvollständiger Lauf erscheint als erfolgreich. Masterfelder bleiben
erhalten; absichtliche Formatverluste sind nachgewiesen statt stillschweigend.

## 0.7.0 – Importabnahme für den Pilotumfang

Zugeordnete Aufgaben: IMPORT-01..03, DATA-08; Entscheidung DEC-02.

Planungsannahme bis zur Entscheidung: EML, MSG und mindestens ein geprüfter
PST-Weg für den Pilot. Ein ausdrücklich auf EML/MSG begrenzter Pilot wäre möglich,
ändert aber nicht das langfristige PST-Ziel. Ungeprüfte Backends zählen nicht
zur Freigabe und müssen im Pilotpaket klar als nicht freigegeben behandelt werden.

1. Nutzbaren PST-Erzeuger und Importweg bereitstellen. Synthetische Archive mit
   bekannten Ordnern, Nachrichten, Empfängern, Zeiten und Anlagen erzeugen.
2. MSG um RTF, eingebettete Nachrichten und weitere Zeichen-/Eigenschaftsvarianten
   erweitern. Nicht unterstützte Elemente müssen sichtbar bleiben.
3. Exchange-/SMTP-Auflösung, Antwortbezüge und Datumsnormalisierung verbessern;
   ungelöste Werte getrennt erhalten. Keine erfundenen Adressen oder Zeitpunkte.
4. Outlook-Lifecycle bei Erfolg, frühem Fehler und Abbruch prüfen. Nur selbst
   eingebundene Teststores entfernen; vorhandene Stores unverändert lassen.
5. Schutz der Original-PST praktisch nachweisen. Falls Outlook beim Öffnen schreibt,
   nur auf einer getrennten Arbeitskopie importieren; Hash/Bezug des Originals und
   Arbeitskopie getrennt dokumentieren. Vorher-/Nachher-Hashprüfung nicht abschalten.

Abnahme: Alle für den Pilot zugesagten Wege lesen gültige synthetische Archive mit
bekannten Sollfeldern. Originaldateien bleiben bytegleich; Hashänderungen und
unlesbare Elemente werden erklärt. Ein erfolgreicher Outlook-Lauf ersetzt keine
libpff-Abnahme und umgekehrt. Fehlt ein zugesagter Weg, bleibt die Version offen.

Zwischenstand vom 11. September: Der echte libpff-Dateipfad ist mit einer
öffentlichen, nicht persönlichen PST-Referenzdatei geprüft; die Quelle blieb
bytegleich. Außerdem besteht eine synthetische MSG ausschließlich mit komprimiertem
RTF-Body und eine echte eingebettete MSG-Unterstruktur. Deren Name und Anzahl
bleiben sichtbar; der nicht exportierte innere Inhalt erzeugt eine Warnung. Das
selbst erzeugte PST-Sollarchiv, Outlook und die Auslieferungsentscheidung für
libpff bleiben offen.

## 0.8.0 – Fehlerfestigkeit und große Läufe

Zugeordnete Aufgaben: RUN-01, RUN-02, PERF-01; Entscheidungen DEC-01.

1. Laufzustand und abgeschlossene Quellen dauerhaft sichern. Nach Prozessabbruch
   einen verwaisten Lauf erkennen und kontrollierte Wiederaufnahme anbieten.
2. Vor Wiederaufnahme Quellenstand, Parser-/Schemaversion und Optionen vergleichen.
   Inkompatible Checkpoints erklären; niemals stillschweigend Daten mischen.
3. Zunächst Wiederaufnahme an Quellengrenzen: Eine unvollständige PST wird erneut
   gelesen, bereits abgeschlossene Quellen nicht. Wiederaufnahme innerhalb einer PST
   wird nur vorgezogen, wenn ihre Wiederholungsdauer das vereinbarte Budget verletzt.
4. Lange Fremdparseroperationen begrenzen. Für unzuverlässig abbrechbare Importwege
   getrennte Workerprozesse mit kontrolliertem Timeout und eigener Ressourcenfreigabe
   vorsehen. Keine fremden Outlook-Prozesse beenden.
5. Prozessabbruch, Parserhänger, beschädigten Cache, Schreibfehler und Platzmangel
   gezielt injizieren; abgeschlossene Laufpakete müssen weiter nutzbar bleiben.
6. Auf festgelegter Referenzhardware kleine, normale und große synthetische Bestände
   messen: frischer Import, Cache, Export, Prüfung, Spitzen-RAM und temporärer Platz.

Abnahme: Fortgesetzter Lauf und ununterbrochener Referenzlauf enthalten dieselben
Nachrichten/Sollfelder ohne neue Duplikate. Neue Lauf-IDs und Zeitstempel dürfen
abweichen. Abbruch hinterlässt kein als vollständig markiertes Teilpaket.

Vorgeschlagene Messmatrix: 1.000 Nachrichten für Funktion, 50.000 als Referenz,
100.000 als Stresstest; zusätzlich große Einzelmails und PST-Dateien. Dateigrößen,
Anlagenmix und Zahl der Quellen werden mit angegeben. PST-Generatoren oder
Stream-Testdoubles ersetzen die tatsächlichen PST-Dateiläufe nicht.

Vor Abschluss werden maximale Archivgröße, RAM-Budget, freier Arbeits-/Exportplatz,
zulässige Laufzeit und Wartezeit beim Abbruch numerisch vereinbart. Ohne diese
Werte gibt es nur Messergebnisse, keine behauptete Leistungsfreigabe.

## 0.9.0-rc.1 – Umzugsschwelle

Zugeordnete Aufgaben: REL-02, OPS-01; Entscheidungen DEC-01, DEC-02, DEC-04, DEC-05.

Für den Umzug müssen alle folgenden Punkte mit einem datierten Nachweis für
denselben Kandidaten erfüllt sein. Aktuell ist diese Gesamtabnahme nicht erreicht.

| Kriterium | Erforderlicher Nachweis |
| --- | --- |
| Quellenschutz | Bytegleiche Originale vor/nach Erfolg, Fehler und Abbruch; Arbeitskopien nachvollziehbar. |
| Vollständigkeit | Vollständige Quellenbilanz und alle Sollnachrichten; keine unerklärten Feldverluste. |
| Pilotformate | Gültige synthetische Dateitests für jeden zugesagten Importweg. |
| Fehlerverhalten | Kein falscher Erfolg bei Parser-, Cache-, Export-, Rechte- und Speicherfehlern. |
| Wiederaufnahme | Abbruch-/Neustarttests mit nachgewiesener Ergebnisgleichheit. |
| Leistung | Vereinbarte Zahlenlimits auf repräsentativer Hardware eingehalten. |
| Windows-Betrieb | Gesamten EXE-Workflow auf sauberem System ohne Python bedienen, einschließlich fremdem Startordner, Abbruch und Neustart. |
| Offline-Betrieb | Gewählter Importweg und Analysepaket bei gesperrtem Netzwerk funktionsfähig. |
| Übertragbarkeit | Laufpaket kopieren; Dateien, Indexverweise und Hashes im neuen Ort prüfen. Originalpfade bleiben Herkunft, keine garantierten lokalen Links. |
| Betriebshilfe | Version, Laufhistorie bzw. Wiederöffnen eines Ergebnisses, verständliche Fehler und kontrollierte Verwaltung eigener Zwischenprodukte. |
| Releasebezug | Quellstand, Build, Abhängigkeiten, Prüfergebnisse und bekannte Grenzen eindeutig verbunden. |
| Fachlicher Testplan | Kleiner Fragen-/Solltrefferkatalog für den Dev-Pilot vorbereitet, zunächst synthetisch erprobt. |

Releaseblocker sind bekannte Quellenänderung, stiller Datenverlust, falscher
Erfolgsstatus, nicht prüfbare Herkunft sowie unbeherrschbare Abbrüche im zugesagten
Umfang. Kleine Darstellungsfehler können mit dokumentierter Auswirkung verbleiben.
Eine offene Pflichtentscheidung wird nicht automatisch durch einen erfolgreichen
Test ersetzt. Der Nutzer entscheidet auf Basis der Abnahme über den tatsächlichen Umzug.

## Dev-Pilot und 1.0.0

Nach bestandener Umzugsschwelle folgt zunächst ein synthetischer Kontrolllauf in
der Dev-Umgebung. Danach werden ausschließlich dort freigegebene Echtdatenkopien
verarbeitet: zuerst ein kleiner manuell prüfbarer Bestand, anschließend ein
repräsentativer Bestand und zuletzt die vereinbarte Zielgröße. Mengen werden vor
dem Pilot festgelegt; ein großer erfolgreicher Lauf ersetzt nicht die Stichprobe.

Je Stufe: Zähler mit dem Ursprungssystem vergleichen, Metadaten/Text/Anlageninventar
stichprobenartig prüfen, Suchfragen anhand der Exporte beantworten und Quelle
zurückverfolgen. Neue Befunde möglichst als synthetische Regression reproduzieren.
Keine Echtdaten oder vertraulichen Diagnosepakete in dieses öffentliche Repository übernehmen.

1.0.0 setzt voraus: keine offenen Releaseblocker, bestandene fachliche Fragen,
bestätigte Betriebsgrenzen und ein vollständig bedienter finaler EXE-Build.
Die Freigabe benennt unterstützte Formate/Backends und bekannte Einschränkungen.

## Spätere Produktversionen

- **1.1.0, Vorschlag:** lokale Volltextsuche, kombinierte Filter, Nachrichtenansicht,
  gespeicherte Suchen und Export ausgewählter Belege. Keine Voraussetzung für den
  Umzug, solange dateibasierte Recherche die Pilotfragen erfüllt.
- **1.2.0, Vorschlag:** Duplikatgruppen mit allen Quellenbezügen, Konversationen,
  Beteiligtennormalisierung; strukturierte Anlagenverarbeitung nach DEC-03.
- **Später:** lokale KI-Recherche erst mit verlässlichen Quellenverweisen und
  festem Evaluationskatalog; keine Pflicht zur Cloud-Anbindung.

## Unmittelbar nächste Arbeitspakete

| Reihenfolge | Paket | Konkretes Ergebnis |
| --- | --- | --- |
| 1 | Baseline und Versionsführung | 0.5.0-Kandidat mit reproduzierbaren Versions-/Buildangaben. |
| 2 | Vollständige Vorprüfung | CHECK-02: ignorierte Dateien sichtbar und gezählt; Auswahlsemantik unverändert. |
| 3 | Quellenbindung | CHECK-01: Vorprüfung, Auswahl und tatsächlicher Import referenzieren denselben Dateistand. |
| 4 | Zielprüfung | CHECK-03: konkrete Pfade, Profilkomponenten und Platzmangel getestet. |
| 5 | Datenvertrag und Exporthärtung | DATA-07/EXPORT-01 als Abschluss von 0.6.0. |

PST-Testumgebung und Zielgrößen werden bereits während dieser Pakete geklärt,
damit sie die spätere Abnahme nicht überraschend blockieren. Die nächsten Schritte
sind damit auch ohne Echtdaten und trotz derzeit fehlender PST-Laufzeit ausführbar.
