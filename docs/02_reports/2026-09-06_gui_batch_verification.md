# MailAnalyst – GUI für große Batchläufe

Datum: 6. September 2026. Ergänzung zum lokalen [Batchblock](2026-09-06_batch_verification.md); keine Veröffentlichung oder Git-Übergabe.

## Umsetzung

Die Verarbeitung zeigt getrennte Phasen für Quellenprüfung, Lesen, Cache, Laufdokumentation, Export, Rückleseprüfung, Ergebnisvorbereitung und Abschluss. Quellenzähler und Nachrichtenzähler sind getrennt; eine Tk-Uhr zeigt die Laufzeit. Die Aktivitätsanzeige bleibt bis zum tatsächlichen Abschluss aktiv, ohne einen unbekannten PST-Gesamtumfang als Prozentzahl darzustellen. Abbruch ist bis zur bestehenden synchronisierten Abschlussgrenze möglich.

Fortschrittsmeldungen werden im Worker gedrosselt und an der GUI-Grenze auf den jeweils neuesten Stand pro Meldungsform zusammengefasst. Abschluss und Fehler bleiben separate Ereignisse. Die Anzeige-Timer werden bei Erfolg, Fehler, Abbruch und Fensterschließen beendet. Der Quellenbericht der gewählten Auswahl wird im Worker geschrieben.

Vorprüfung und Ergebnisse rendern jeweils höchstens 500 Tabellenzeilen und besitzen Seitenwechsel, Statusfilter, Mindestbreiten und Scrollbars. Die Quellenliste bleibt eine vollständige Metadatenliste; die Auswahl ist über stabile Originalindizes auch nach Filtern und Blättern korrekt. Aktionen zum Ein-/Ausschließen von Warnungen betreffen alle Quellen.

GUI-Läufe schreiben vor Veröffentlichung `exports/review.sqlite3`. Dieser kompakte Index enthält Datum, Absender, Betreff, Format, Status, Fehlertext und Herkunft, aber keine Mailtexte. Er wird als Export gehasht. Die Ergebnisansicht liest ihn schreibgeschützt in Seiten und erschließt damit auch Fehler nach der ersten Vorschau. Ein Doppelklick zeigt die Herkunft und den Fehlertext. Die CLI erzeugt diesen zusätzlichen GUI-Index nicht.

## Automatisierte Nachweise

Windows mit der vorhandenen Repository-Umgebung; ausschließlich synthetische Daten. Der vollständige Testlauf bestand mit **58 Tests**, ohne übersprungene Tests, in 11,84 Sekunden. Compileall und `pip check` waren erfolgreich. Die 200-Zeilen-Grenze und azyklische Paketimporte werden von den Tests geprüft. Die bisherigen Export-Snapshots blieben unverändert.

Neue beziehungsweise erweiterte Nachweise:

- 50.000 synthetische Quellenmetadaten in der echten Tk-Vorprüfung: 500 sichtbare Einträge, korrekter Seitenwechsel, Auswahl auf der zweiten Seite und Warnungsfilter mit globalem Ausschluss.
- Vollständiger Python-GUI-Lauf mit 1.201 Nachrichten aus einem PST-Testdouble: drei Ergebnisseiten und gezielter Zugriff auf den Fehler an Position 1.201.
- Sichtbare Exportphase mit aktiver Anzeige und Nachrichtenzähler; Abbruch während des Exports erzeugt `cancelled` und veröffentlicht keine Teilausgabe.
- 50.000 Fortschrittsmeldungen: Die GUI erhält den letzten Zählerstand, ohne jede Zwischenmeldung einzeln abarbeiten zu müssen.
- Ergebnisindex lässt sich separat kopieren und schreibgeschützt mit Seiten-/Fehlerfilter lesen; Mailtextfelder sind ausgeschlossen. Der Index ist in den Manifest-Exporten enthalten.
- Service meldet Lesen, Export, Validierung und Abschluss in passenden Phasen. Bestehende Tests für Mehrfachstarts, geordnetes Schließen, Cache und Exportintegrität bestehen weiterhin.

Bei der Umsetzung wurde ein Timerproblem beim Schließen gefunden: Der interne Progressbar-Timer muss vor der allgemeinen Tk-Timerbereinigung gestoppt werden. Dies wurde korrigiert und der Schließtest erneut erfolgreich ausgeführt. Die Testfixture sammelt außerdem zerstörte Tk-Interpreterzyklen vor dem nächsten Test ausdrücklich im Hauptthread; damit wird eine während einer Zwischenprüfung beobachtete threadfremde Tcl-Freigabe vermieden. Das ersetzt keine native EXE-Bedienabnahme.

## Vollständiger Großlauf und Build

Der abschließende Großlauf verwendet die 50.000 tatsächlich erzeugten synthetischen EML-Dateien des vorherigen Batchbenchmarks. Er durchläuft die echte Python-Tk-Ereignisschleife mit ausgeblendetem Fenster, Systemcheck, Vorprüfung, Analysepaket, Ergebnisindex und Navigation zur letzten Seite. Der Lauf war erfolgreich: 50.000 Nachrichten, null Parserfehler, Status `completed`, letzte angezeigte Zeile 50.000 und korrekt leerer Fehlerfilter. Gesamtdauer einschließlich Vorprüfung: 394,73 Sekunden (rund 6:35 Minuten). Die GUI-Callbacks beobachteten Lesen, Cache, Dokumentation, Export, Prüfung, Ergebnisvorbereitung und Abschluss; es wurden keine Callbackfehler registriert. Dies ist eine lokale Funktionsmessung unter nicht isolierter Hintergrundlast, keine garantierte Laufzeit. Rohbericht und Paket liegen im ignorierten Ordner `out/gui-batch-large-xf2d15on`, Konsolenprotokoll unter `out/gui-batch-large.log`. Das Testfenster wurde geschlossen.

Der abschließende Windows-Build mit `build_exe.ps1` war erfolgreich (Exitcode 0); auszuliefern ist der gesamte Ordner `dist/MailAnalyst`. Die native Bedienprüfung der gebauten EXE ist in dieser Sitzung nicht möglich, weil die verfügbaren Computer-Use-Werkzeuge keine native Windows-App-Steuerung anbieten. Ein erfolgreicher Build beziehungsweise ausgeblendeter Python-Tk-Test wird nicht als vollständige EXE-Abnahme bezeichnet.

## Grenzen und Dokumentation

Reale PST-/MSG-Importwege, frühe Outlook-Lifecycle-Fehler, Wiederaufnahme nach Prozessabbruch und die fachliche Abnahme bleiben offen. Ein Ergebnisfilter erschließt nur den kompakten Index, keine Volltextrecherche. Quellenmetadaten bleiben größenabhängig; Seitenbegrenzung garantiert keine feste Gesamt-RAM-Grenze. Der Ergebnisindex enthält vertrauliche Metadaten und gehört wie andere Exporte nicht in Git.

README, Architektur, Datenmodell, STATUS und der Repository-Prüfskill wurden an Phasen, Seitenfilter und Ergebnisindex angepasst. PROJECT_GOALS wurde für diesen GUI-Block geprüft; es gibt keine neue fachliche Zieländerung. Historische Berichte bleiben unverändert. Die Dokumentationsprüfung umfasst geänderte Aussagen und 45 lokale Links in sieben betroffenen Dokumenten; alle geprüft. `git diff --check` war erfolgreich. Commit und Push wurden nicht ausgeführt.
