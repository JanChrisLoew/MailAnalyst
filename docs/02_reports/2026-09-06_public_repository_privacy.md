# Datenschutzprüfung des öffentlichen Repositorys

Stand: 6. September 2026; geprüfter veröffentlichter Stand `a469b09`. Der Bericht wiederholt keine persönlichen Adressen oder vollständigen Autorennamen.

## Umfang und Befunde

- Fünf lokal erreichbare veröffentlichte Commits, 132 unterschiedliche Kombinationen aus Blob und Pfad sowie Autor-/Committermetadaten geprüft. Die Ausgangshistorie enthielt persönliche Identitätsangaben; ein normaler Folgecommit hätte diese nicht entfernt.
- Musterprüfung auf bekannte Token-/Schlüsselformate, Credential-Zuweisungen, Mailadressen, Benutzerverzeichnisse und URLs; Dokumentation und synthetische Daten zusätzlich inhaltlich gesichtet. Keine erkennbaren Zugangsdaten, privaten Benutzerpfade, Kunden-/Projektnamen oder echten Mailarchive in den geprüften Dateien gefunden. Die beiden Binärdateien sind die gebündelten Mulish-Schriftdateien; keine allgemeine Binär-Forensik durchgeführt.
- Die fachliche Beschreibung von spezifischen betrieblichen Abläufen und Gestaltungsvorgaben war in früheren Dokumentfassungen enthalten. Dieser Kontext wurde mit Freigabe durch allgemeine Produktbeschreibungen ersetzt; funktionale Anforderungen und Programmverhalten bleiben erhalten.
- GitHub-Abfrage: öffentliches Repository, ein Branch (`main`), keine Tags, Releases, Actions-Artefakte, Issues oder Pull Requests; keine von GitHub ausgewiesenen Forks. Zwei Actions-Läufe und deren Logs geprüft. Gefundene Benutzerpfade gehören ausschließlich zu GitHub-Runnern; keine erkennbaren persönlichen E-Mail-Adressen oder Tokenmuster in diesen Logs.
- GitHub meldet Secret-Scanning und Secret-Scanning-Push-Protection als aktiviert. Diese Funktionen schützen nicht vor beliebigen personenbezogenen Angaben oder fachlichen Interna.

## Lokal vorbereitete Prävention

`.gitignore` um Mail-/Archiv-, Cache-, Tabellen-/Export-, Log- und Credentialmuster sowie private Arbeitsverzeichnisse erweitert. `git check-ignore --no-index` bestätigt repräsentative Pfade einschließlich alternativer Zielordner. README enthält Hinweise zur Kontrolle des Git-Index und einer bewusst gewählten öffentlichen Commitidentität. Die Präventionsänderungen gehören zum Bereinigungscommit.

## Freigegebene Bereinigung

Die lokale Commitidentität verwendet den öffentlichen GitHub-Benutzernamen und die kontobezogene Noreply-Adresse. Autor und Committer der bisherigen Commits werden entsprechend ersetzt. Die historischen Dokumentfassungen werden von betrieblichen Kontextangaben bereinigt; Code, Tests, Schriftdateien und Lizenzen bleiben dabei bytegleich erhalten. Historische Commitverweise in der Dokumentation werden soweit möglich auf die bereinigten Vorgänger übertragen.

Die bisherige Historie ist ausschließlich lokal im ignorierten Ausgabebereich gesichert. Die neue Historie wird vor der Veröffentlichung auf Identitätsangaben und übrig gebliebene Kontextbegriffe geprüft. Die Veröffentlichung erfolgt ausschließlich für `main` mit einer an den geprüften Remote-Commit gebundenen Force-Push-Sperre. Den tatsächlichen Synchronisationsstand mit `git status` und `git log` prüfen.

Externe Klone, alte Actions-Läufe und GitHub-Caches können weiterhin auf alte Commitobjekte verweisen. Die Historienumschreibung garantiert keine vollständige Löschung bereits veröffentlichter Angaben; gegebenenfalls ist eine weitere Klärung mit GitHub erforderlich.

## Grenzen und Dokumentationsprüfung

Musterprüfung und manuelle Sichtung sind keine Garantie, jedes denkbare Geheimnis zu erkennen. Nicht geprüft: Inhalte fremder Klone, nicht erreichbare Serverobjekte, GitHub-Wiki und öffentliches Benutzerprofil. Keine Mailbestände außerhalb der versionierten Dateien gelesen. Kein spezialisierter Secretscanner installiert.

Ausschlussregeln, Dokumentation und Git-Metadaten geändert; kein verändertes Anwendungsverhalten. Ignore-Regeln, Diff und lokale Dokumentationsverweise geprüft; keine erneute Funktions-/Buildabnahme erforderlich. Die erfolgreichen GitHub-CI-Läufe wurden bei dieser Prüfung erstmals remote bestätigt, unabhängig von den historischen Angaben früherer Berichte.

Historische Commitverweise wurden auf die bereinigten Versionen übertragen. Frühere Test-/CI-Nachweise beziehen sich auf deren funktional identischen Stand vor der Umschreibung, nicht auf bereits damals existierende neue Commit-IDs.
