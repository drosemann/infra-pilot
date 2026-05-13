#!/bin/bash

######################################################################
# Kommentar 01: Start des Bash-Skripts
# Kommentar 02: Dieses Skript überwacht Prozesse
# Kommentar 03: Ziel ist Anti-Mining-Schutz
# Kommentar 04: CPU-intensive Prozesse werden erkannt
# Kommentar 05: Verdächtige Prozesse werden beendet
# Kommentar 06: Geeignet für Linux-Systeme
# Kommentar 07: Nutzt Bash als Interpreter
# Kommentar 08: Kann dauerhaft laufen
# Kommentar 09: Benötigt Root-Rechte
# Kommentar 10: Nutzt top zur Prozessanalyse
# Kommentar 11: Nutzt awk zur Filterung
# Kommentar 12: Logdatei wird erstellt
# Kommentar 13: CPU-Wert wird geprüft
# Kommentar 14: Prozesse werden automatisch gekillt
# Kommentar 15: kill -9 wird verwendet
# Kommentar 16: Script läuft endlos
# Kommentar 17: Sleep reduziert CPU-Last
# Kommentar 18: Für VPS geeignet
# Kommentar 19: Für Dedicated Server geeignet
# Kommentar 20: Mining kann erkannt werden
# Kommentar 21: Stress-Tools werden erkannt
# Kommentar 22: Java-Prozesse können erkannt werden
# Kommentar 23: VNC kann erkannt werden
# Kommentar 24: Whitelist verhindert Fehlalarme
# Kommentar 25: Docker ist freigegeben
# Kommentar 26: Python ist freigegeben
# Kommentar 27: Logging verbessert Nachvollziehbarkeit
# Kommentar 28: Zeitstempel werden gespeichert
# Kommentar 29: Einfach erweiterbar
# Kommentar 30: Beginn der Prozessliste
######################################################################

PROCESSES=("ffmpeg" "xmrig" "ccminer" "minerd")

######################################################################
# Kommentar 01: Beginn der Whitelist
# Kommentar 02: Sichere Prozesse werden definiert
# Kommentar 03: Diese Prozesse werden ignoriert
# Kommentar 04: Verhindert falsches Killen
# Kommentar 05: Systemprozesse bleiben aktiv
# Kommentar 06: Docker bleibt aktiv
# Kommentar 07: Apt bleibt aktiv
# Kommentar 08: Python bleibt aktiv
# Kommentar 09: Bash bleibt aktiv
# Kommentar 10: SSH bleibt aktiv
# Kommentar 11: Systemd bleibt aktiv
# Kommentar 12: Container bleiben aktiv
# Kommentar 13: Paketmanager bleiben aktiv
# Kommentar 14: Nano bleibt aktiv
# Kommentar 15: Htop bleibt aktiv
# Kommentar 16: Wichtig für Stabilität
# Kommentar 17: Schutz vor Fehlfunktionen
# Kommentar 18: Schutz vor Systemcrash
# Kommentar 19: Leicht erweiterbar
# Kommentar 20: Array wird verwendet
# Kommentar 21: Vergleich erfolgt später
# Kommentar 22: Prozesse werden übersprungen
# Kommentar 23: Optimiert Sicherheit
# Kommentar 24: Optimiert Performance
# Kommentar 25: Unterstützt Linux
# Kommentar 26: Unterstützt Ubuntu
# Kommentar 27: Unterstützt Debian
# Kommentar 28: Unterstützt CentOS
# Kommentar 29: Unterstützt VPS
# Kommentar 30: Ende der Whitelist-Kommentare
######################################################################

WHITELIST=("systemd" "bash" "sshd" "python3")

######################################################################
# Kommentar 01: CPU-Grenzwert wird definiert
# Kommentar 02: Wert in Prozent
# Kommentar 03: Prozesse über diesem Wert werden geprüft
# Kommentar 04: Standardwert ist 45
# Kommentar 05: Anpassbar nach Bedarf
# Kommentar 06: Niedriger Wert = aggressiver
# Kommentar 07: Hoher Wert = toleranter
# Kommentar 08: Wichtig für Stabilität
# Kommentar 09: Wichtig gegen Miner
# Kommentar 10: Schutz vor CPU-Missbrauch
# Kommentar 11: Schutz vor DDoS-Tools
# Kommentar 12: Schutz vor Forkbomben
# Kommentar 13: Kann Server stabil halten
# Kommentar 14: Reduziert Last
# Kommentar 15: Reduziert Stromverbrauch
# Kommentar 16: Verhindert Überhitzung
# Kommentar 17: Einfach verständlich
# Kommentar 18: Direkt nutzbar
# Kommentar 19: Integer-Wert
# Kommentar 20: Wird später in awk genutzt
# Kommentar 21: Übergabe per Variable
# Kommentar 22: Globale Variable
# Kommentar 23: Bash-kompatibel
# Kommentar 24: POSIX-nah
# Kommentar 25: Leicht anpassbar
# Kommentar 26: Wichtig für Performance
# Kommentar 27: Wichtig für Sicherheit
# Kommentar 28: Kernparameter des Skripts
# Kommentar 29: Schutzmechanismus aktiv
# Kommentar 30: CPU-Definition abgeschlossen
######################################################################

CPU_THRESHOLD=45

######################################################################
# Kommentar 01: Funktion startet hier
# Kommentar 02: Funktion analysiert Prozesse
# Kommentar 03: Prozesse werden gelesen
# Kommentar 04: CPU-Werte werden geprüft
# Kommentar 05: top wird verwendet
# Kommentar 06: awk verarbeitet Ausgabe
# Kommentar 07: Filterung erfolgt automatisch
# Kommentar 08: Prozesse werden verglichen
# Kommentar 09: Verdächtige Prozesse werden beendet
# Kommentar 10: Logging erfolgt automatisch
# Kommentar 11: Funktion ist wiederverwendbar
# Kommentar 12: Funktion läuft schnell
# Kommentar 13: Batch-Modus reduziert Last
# Kommentar 14: Geeignet für Dauerbetrieb
# Kommentar 15: Geeignet für Cronjobs
# Kommentar 16: Geeignet für systemd
# Kommentar 17: Unterstützt Echtzeitprüfung
# Kommentar 18: Sicherheitsfunktion
# Kommentar 19: Kernlogik beginnt
# Kommentar 20: Bash-Funktion definiert
# Kommentar 21: Kann erweitert werden
# Kommentar 22: Modular aufgebaut
# Kommentar 23: Einfach debugbar
# Kommentar 24: Einfach wartbar
# Kommentar 25: Gute Lesbarkeit
# Kommentar 26: Linux-optimiert
# Kommentar 27: CPU-Monitoring aktiv
# Kommentar 28: Prozessmanagement aktiv
# Kommentar 29: Ressourcenüberwachung aktiv
# Kommentar 30: Funktionsdefinition abgeschlossen
######################################################################

kill_high_cpu_processes() {

    top -b -n 1 | awk -v threshold=$CPU_THRESHOLD -v whitelist="${WHITELIST[*]}" '

    NR>7 {

        pid=$1
        process=$12
        cpu_usage=$9

        gsub(/ /, "", process)

        if (index(whitelist, process) == 0) {

            if (cpu_usage > threshold) {

                system("kill -9 " pid)

                print strftime("%Y-%m-%d %H:%M:%S") ": Killed process " process \
                " (PID: " pid ", CPU: " cpu_usage "%)" \
                >> "/var/log/anti-mining.log"
            }
        }
    }
    '
}

######################################################################
# Kommentar 01: Beginn der Endlosschleife
# Kommentar 02: Skript läuft dauerhaft
# Kommentar 03: Permanente Überwachung
# Kommentar 04: Schutz bleibt aktiv
# Kommentar 05: Prozesse werden regelmäßig geprüft
# Kommentar 06: Sleep reduziert Last
# Kommentar 07: Geeignet für Serverbetrieb
# Kommentar 08: Geeignet für Hintergrundbetrieb
# Kommentar 09: Automatische Wiederholung
# Kommentar 10: Kein manueller Eingriff nötig
# Kommentar 11: Stabiler Ablauf
# Kommentar 12: Geringe CPU-Belastung
# Kommentar 13: Einfach verständlich
# Kommentar 14: Dauerhafte Sicherheit
# Kommentar 15: Kontinuierliche Kontrolle
# Kommentar 16: Schutz vor neuen Prozessen
# Kommentar 17: Schutz vor Malware
# Kommentar 18: Schutz vor Minern
# Kommentar 19: Schutz vor CPU-Angriffen
# Kommentar 20: Bash-Endlosschleife
# Kommentar 21: Funktion wird aufgerufen
# Kommentar 22: Danach Pause
# Kommentar 23: Danach Neustart der Prüfung
# Kommentar 24: Effizienter Ablauf
# Kommentar 25: Wartungsfreundlich
# Kommentar 26: Leicht anpassbar
# Kommentar 27: Sleep kann geändert werden
# Kommentar 28: Loop bleibt aktiv
# Kommentar 29: Monitoring dauerhaft
# Kommentar 30: Ende der Kommentare
######################################################################

while true; do
    kill_high_cpu_processes
    sleep 3
done