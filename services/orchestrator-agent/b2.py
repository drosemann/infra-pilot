# Importiert das Logging-Modul zur Protokollierung von Ereignissen im Bot
# Das Logging-Modul wird verwendet um Debug-, Info-, Warning- und Error-Meldungen zu protokollieren
# Ermöglicht strukturierte Protokollierung von Ereignissen für besseres Troubleshooting
# Kann in Dateien, Konsole oder andere Handler schreiben
# Unterstützt verschiedene Log-Level und Formatierung
# Essentiell für Production-Umgebungen zur Fehlerbehandlung und Monitoring
# Ermöglicht asynchrone und synchrone Protokollierung
# Kann mit verschiedenen Filtern konfiguriert werden
# Unterstützt Thread-sichere Operationen
# Ermöglicht strukturierte Log-Ausgaben in verschiedenen Formaten
# Integriert sich gut mit anderen Python-Modulen
# Kann mit Rotatoren für automatische Dateirotation konfiguriert werden
# Ermöglicht das Filtern von Logs nach Modul oder Logger-Name
# Kann mit mehreren Handlern arbeiten für verschiedene Ziele
# Unterstützt hierarchische Logger-Strukturen
# Ermöglicht kontextbezogenes Logging mit Extra-Daten
# Kann mit Decorators für funktionales Logging verwendet werden
# Bietet Performance-optimierte Logging-Optionen
# Ermöglicht das Erfassen von Exception-Stacks automatisch
# Kann mit Custom-Formatternn erweitert werden
# Unterstützt Internationalisierung von Log-Meldungen
# Ermöglicht zeitbasierte Rotation von Log-Dateien
# Kann mit verschiedenen Encoding-Optionen konfiguriert werden
# Bietet NullHandler für Library-Logging Best-Practices
# Kann mit Context-Variablen für Thread-lokale Daten arbeiten
# Ermöglicht das Deaktivieren bestimmter Logger-Module
# Unterstützt Lazy-Evaluation von teuren Log-Meldungen
import logging

# Importiert subprocess zur Ausführung externer Shell-Befehle
import subprocess

# Importiert sys für den Zugriff auf Python-Systemfunktionen
import sys

# Importiert os für Betriebssystem-Funktionen und Umgebungsvariablen
import os

# Importiert re für reguläre Ausdrücke und Pattern-Matching
import re

# Importiert time für Zeitfunktionen und Verzögerungen
import time

# Importiert concurrent.futures für parallele Verarbeitung
import concurrent.futures

# Importiert random zur Generierung zufälliger Werte
import random

# Importiert die Discord-Bibliothek
import discord

# Importiert Command- und Task-Funktionen von discord.ext
from discord.ext import commands, tasks

# Importiert die Docker-Python-Bibliothek
import docker

# Importiert asyncio für asynchrone Programmierung
import asyncio

# Importiert app_commands für Discord Slash Commands
from discord import app_commands

# Importiert requests für HTTP-API-Anfragen
import requests

# Importiert Datums- und Zeitfunktionen
from datetime import datetime, timedelta

# Importiert Lock für Thread-Synchronisierung
from threading import Lock

# =============================================================================
# Configuration Section
# =============================================================================

# Lädt den Discord Bot Token aus den Umgebungsvariablen
TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")

# Definiert das RAM-Limit pro VPS-Instanz
RAM_LIMIT = '1g'

# Definiert die maximale Anzahl an VPS pro Benutzer
SERVER_LIMIT = 1

# Definiert die Datei zur Speicherung der Datenbankeinträge
database_file = 'database.txt'

# Erstellt Standard-Discord-Intents
intents = discord.Intents.default()

# Deaktiviert Nachrichten-Events zur Performance-Optimierung
intents.messages = False

# Deaktiviert Zugriff auf Nachrichteninhalte
intents.message_content = False

# Erstellt den Discord-Bot mit Prefix und Intents
bot = commands.Bot(command_prefix='/', intents=intents)

# Initialisiert den Docker-Client aus der Umgebung
client = docker.from_env()

# Erstellt eine Whitelist für Admin-Benutzer
whitelist_ids = set(filter(None, os.getenv("WHITELIST_IDS", "").split(",")))

# Erstellt einen Lock für sichere Datenbankzugriffe
database_lock = Lock()

# Definiert ein Regex-Muster für sichere Containernamen
SAFE_CONTAINER_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")

# =============================================================================
# Utility Functions for Database Management
# =============================================================================

# Fügt neue VPS-Daten in die Datenbankdatei ein
def add_to_database(userid, container_name, ssh_command):

    # Beschreibung der Funktion
    """
    Append instance details (user ID, container identifier, SSH command) to the database file.
    """

    # Sperrt die Datenbank während des Schreibens
    with database_lock:

        # Öffnet die Datenbankdatei im Anhängemodus
        with open(database_file, 'a', encoding='utf-8') as f:

            # Schreibt die VPS-Daten in die Datei
            f.write(f"{userid}|{container_name}|{ssh_command}\n")

# Entfernt einen Datenbankeintrag anhand des SSH-Befehls
def remove_from_database(ssh_command):

    # Beschreibung der Funktion
    """
    Remove an entry containing the specified SSH command from the database.
    """

    # Prüft ob die Datenbankdatei existiert
    if not os.path.exists(database_file):

        # Beendet die Funktion wenn Datei fehlt
        return

    # Sperrt die Datenbank während des Schreibens
    with database_lock:

        # Öffnet die Datei zum Lesen
        with open(database_file, 'r', encoding='utf-8') as f:

            # Liest alle Zeilen der Datei
            lines = f.readlines()

        # Öffnet die Datei zum Überschreiben
        with open(database_file, 'w', encoding='utf-8') as f:

            # Iteriert über alle Zeilen
            for line in lines:

                # Prüft ob der SSH-Befehl nicht enthalten ist
                if ssh_command not in line:

                    # Schreibt gültige Zeilen zurück
                    f.write(line)

# Gibt alle Server eines Benutzers zurück
def get_user_servers(user):

    # Beschreibung der Funktion
    """
    Retrieve all VPS instance records associated with a given user.
    """

    # Prüft ob die Datenbankdatei existiert
    if not os.path.exists(database_file):

        # Gibt eine leere Liste zurück
        return []

    # Erstellt eine leere Liste für Server
    servers = []

    # Öffnet die Datenbankdatei
    with open(database_file, 'r') as f:

        # Iteriert durch alle Zeilen
        for line in f:

            # Prüft ob die Zeile mit der Benutzer-ID beginnt
            if line.startswith(user):

                # Fügt den Server zur Liste hinzu
                servers.append(line.strip())

    # Gibt die Serverliste zurück
    return servers

# Zählt die Anzahl der Server eines Benutzers
def count_user_servers(userid):

    # Beschreibung der Funktion
    """
    Count the number of active VPS instances a user currently has.
    """

    # Gibt die Anzahl der Server zurück
    return len(get_user_servers(userid))