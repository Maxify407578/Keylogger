import sys
from datetime import datetime
import uuid
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, colorchooser
import time
import threading
import random
import os
import json
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from PIL import Image, ImageTk
import webbrowser
from fpdf import FPDF
import pyautogui
import base64
import hashlib
from cryptography.fernet import Fernet
import http.server
import socketserver
import socket
from flask import Flask, request, jsonify

# Globale Konstanten
VERSION = "2.0"
CONFIG_FILE = "keylogger_config.json"
BACKUP_DIR = "backups"
SERVER_PORT = 8000

app = Flask(__name__)

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/pay.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def log_message(self, format, *args):
        # Unterdrücke Server-Logs
        pass

class PasswordManager:
    """Verwaltet die Speicherung und Verschlüsselung von Passwörtern."""
    def __init__(self):
        self.key = None
        self.cipher_suite = None
        self.passwords = {}
        self.initialize()
        
    def initialize(self):
        """Initialisiert den Passwortmanager, erstellt oder lädt den Schlüssel."""
        # Erstelle einen Schlüssel oder lade ihn
        key_file = "key.key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(self.key)
                
        self.cipher_suite = Fernet(self.key)
        
        # Lade gespeicherte Passwörter
        if os.path.exists("passwords.enc"):
            try:
                with open("passwords.enc", "rb") as f:
                    encrypted_data = f.read()
                    decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                    self.passwords = json.loads(decrypted_data.decode())
            except:
                self.passwords = {}
                
    def add_password(self, service, username, password):
        """Fügt ein neues Passwort für einen Dienst hinzu."""
        self.passwords[service] = {
            "username": username,
            "password": password
        }
        self.save_passwords()
        
    def get_password(self, service):
        """Gibt das Passwort für einen Dienst zurück."""
        return self.passwords.get(service, None)
        
    def delete_password(self, service):
        """Löscht das Passwort für einen Dienst."""
        if service in self.passwords:
            del self.passwords[service]
            self.save_passwords()
            return True
        return False
        
    def save_passwords(self):
        """Speichert die Passwörter in einer verschlüsselten Datei."""
        encrypted_data = self.cipher_suite.encrypt(json.dumps(self.passwords).encode())
        with open("passwords.enc", "wb") as f:
            f.write(encrypted_data)
            
    def get_all_services(self):
        """Gibt eine Liste aller gespeicherten Dienste zurück."""
        return list(self.passwords.keys())

class StatisticsWindow:
    def __init__(self, parent, log_sessions, key_count):
        self.window = tk.Toplevel(parent)
        self.window.title('📊 Keylogger Statistiken')
        self.window.geometry('800x600')
        self.window.resizable(True, True)
        
        self.colors = {
            'bg': '#1E272E',
            'fg': '#D6E0F0',
            'accent': '#3498DB',
            'success': '#2ECC71',
            'danger': '#E74C3C',
            'warning': '#F39C12',
            'neutral': '#95A5A6',
            'card_bg': '#2C3E50'
        }
        
        self.window.configure(bg=self.colors['bg'])
        self.log_sessions = log_sessions
        self.total_keys = key_count
        
        self.init_ui()
        
    def init_ui(self):
        # Hauptcontainer
        container = tk.Frame(self.window, bg=self.colors['bg'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Titel
        title = tk.Label(
            container,
            text='📊 Detaillierte Statistiken',
            font=('Arial', 24, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['bg']
        )
        title.pack(pady=(0, 20))
        
        # Statistik-Karten
        stats_frame = tk.Frame(container, bg=self.colors['bg'])
        stats_frame.pack(fill='both', expand=True)
        
        # Linke Spalte
        left_frame = tk.Frame(stats_frame, bg=self.colors['bg'])
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Allgemeine Statistiken
        self.create_stat_card(left_frame, 'Allgemeine Statistiken', [
            f'Gesamte Tastenanschläge: {self.total_keys}',
            f'Durchschnitt pro Sitzung: {self.get_avg_keys_per_session():.1f}',
            f'Anzahl Sitzungen: {len(self.log_sessions)}',
            f'Gesamte Logging-Zeit: {self.get_total_time()}'
        ])
        
        # Sitzungs-Statistiken
        session_stats = self.create_stat_card(left_frame, 'Letzte Sitzungen', [
            self.format_session(session) for session in self.log_sessions[-5:]
        ])
        
        # Rechte Spalte
        right_frame = tk.Frame(stats_frame, bg=self.colors['bg'])
        right_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # Grafische Statistiken
        self.create_graph(right_frame)
        
        # Export-Button
        export_frame = tk.Frame(container, bg=self.colors['bg'])
        export_frame.pack(fill='x', pady=(20, 0))
        
        export_btn = tk.Button(
            export_frame,
            text='📊 Als PDF exportieren',
            command=self.export_stats,
            font=('Arial', 12),
            bg=self.colors['accent'],
            fg=self.colors['fg'],
            relief='flat',
            padx=15,
            pady=8
        )
        export_btn.pack(side='right')
        
    def create_stat_card(self, parent, title, stats):
        card = tk.Frame(parent, bg=self.colors['card_bg'], padx=15, pady=15)
        card.pack(fill='x', pady=(0, 15))
        
        # Titel
        tk.Label(
            card,
            text=title,
            font=('Arial', 16, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['card_bg']
        ).pack(anchor='w', pady=(0, 10))
        
        # Statistiken
        for stat in stats:
            tk.Label(
                card,
                text=stat,
                font=('Arial', 12),
                fg=self.colors['fg'],
                bg=self.colors['card_bg']
            ).pack(anchor='w', pady=2)
            
    def create_graph(self, parent):
        # Erstelle Matplotlib-Figur
        fig = Figure(figsize=(6, 4), facecolor=self.colors['card_bg'])
        ax = fig.add_subplot(111)
        
        # Daten vorbereiten
        sessions = min(len(self.log_sessions), 10)  # Letzte 10 Sitzungen
        x = range(sessions)
        y = [s['key_count'] for s in self.log_sessions[-sessions:]]
        
        # Plot erstellen
        ax.bar(x, y, color=self.colors['accent'])
        ax.set_facecolor(self.colors['card_bg'])
        ax.set_title('Tastenanschläge pro Sitzung', color=self.colors['fg'])
        ax.set_xlabel('Sitzung', color=self.colors['fg'])
        ax.set_ylabel('Tastenanschläge', color=self.colors['fg'])
        
        # Achsen anpassen
        ax.tick_params(colors=self.colors['fg'])
        ax.spines['bottom'].set_color(self.colors['fg'])
        ax.spines['top'].set_color(self.colors['fg'])
        ax.spines['left'].set_color(self.colors['fg'])
        ax.spines['right'].set_color(self.colors['fg'])
        
        # Canvas erstellen
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
    def get_avg_keys_per_session(self):
        if not self.log_sessions:
            return 0
        return self.total_keys / len(self.log_sessions)
        
    def get_total_time(self):
        total_seconds = sum(
            (s['duration'].total_seconds() for s in self.log_sessions)
        )
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
        
    def format_session(self, session):
        duration = session['duration']
        minutes = int(duration.total_seconds() // 60)
        return f"Sitzung vom {session['start'].strftime('%d.%m.%Y %H:%M')} - {session['key_count']} Tasten in {minutes}min"
        
    def export_stats(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"keylogger_stats_{timestamp}.pdf"
            
            pdf = FPDF()
            pdf.add_page()
            
            # Titel
            pdf.set_font('Arial', 'B', 24)
            pdf.cell(0, 20, 'Keylogger Statistiken', ln=True, align='C')
            
            # Allgemeine Stats
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 15, 'Allgemeine Statistiken:', ln=True)
            
            pdf.set_font('Arial', '', 12)
            stats = [
                f'Gesamte Tastenanschläge: {self.total_keys}',
                f'Durchschnitt pro Sitzung: {self.get_avg_keys_per_session():.1f}',
                f'Anzahl Sitzungen: {len(self.log_sessions)}',
                f'Gesamte Logging-Zeit: {self.get_total_time()}'
            ]
            
            for stat in stats:
                pdf.cell(0, 10, stat, ln=True)
                
            pdf.output(filename)
            
            messagebox.showinfo(
                '✅ Erfolg',
                f'Statistiken wurden als PDF exportiert:\n{filename}'
            )
            
        except Exception as e:
            messagebox.showerror(
                '❌ Fehler',
                f'Fehler beim Exportieren: {e}'
            )

class LoginWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('🔐 Keylogger Pro')
        self.root.geometry('400x450')
        self.root.resizable(False, False)
        
        # Passwort festlegen
        self.correct_password = "2142"
        self.hacker_password = "5435436"  # Neuer Hacker-Modus PIN
        self.max_attempts = 3
        self.current_attempts = 0
        
        # Farben und Stile
        self.colors = {
            'bg': '#1E272E',
            'fg': '#D6E0F0',
            'accent': '#3498DB',
            'success': '#2ECC71',
            'danger': '#E74C3C',
            'input_bg': '#2C3A47',
            'neutral': '#95A5A6'
        }
        
        # Window-Stil
        self.root.configure(bg=self.colors['bg'])
        
        # Icon setzen
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
            
        # Zentrieren auf dem Bildschirm
        self.center_window()
        
        # Erstelle Backup-Verzeichnis
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
            
        self.init_ui()
        
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def init_ui(self):
        # Hauptframe
        main_frame = tk.Frame(self.root, bg=self.colors['bg'], padx=30, pady=30)
        main_frame.pack(fill='both', expand=True)
        
        # Logo/Titel
        logo_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        logo_frame.pack(pady=(0, 20))
        
        # Version
        version_label = tk.Label(
            logo_frame,
            text=f'v{VERSION}',
            font=('Arial', 8),
            fg=self.colors['neutral'],
            bg=self.colors['bg']
        )
        version_label.pack(anchor='e')
        
        logo_title = tk.Label(
            logo_frame,
            text='🔐 Keylogger Pro',
            font=('Arial', 24, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['bg']
        )
        logo_title.pack()
        
        subtitle = tk.Label(
            logo_frame,
            text='Sicherheitsauthentifizierung',
            font=('Arial', 12),
            fg=self.colors['fg'],
            bg=self.colors['bg']
        )
        subtitle.pack(pady=(5, 0))
        
        # Passwort-Frame
        password_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        password_frame.pack(pady=20)
        
        # Passwort Label
        password_label = tk.Label(
            password_frame,
            text='Bitte PIN-Code eingeben:',
            font=('Arial', 12),
            fg=self.colors['fg'],
            bg=self.colors['bg'],
            anchor='w'
        )
        password_label.pack(fill='x', pady=(0, 10))
        
        # Passwort-Eingabe
        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(
            password_frame,
            textvariable=self.password_var,
            font=('Arial', 14),
            bg=self.colors['input_bg'],
            fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            width=15,
            show='•',
            justify='center'
        )
        self.password_entry.pack(pady=5)
        self.password_entry.focus()
        
        # Status-Label
        self.status_label = tk.Label(
            password_frame,
            text='',
            font=('Arial', 10),
            fg=self.colors['danger'],
            bg=self.colors['bg']
        )
        self.status_label.pack(pady=5)
        
        # Button-Frame
        button_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        button_frame.pack(pady=10)
        
        # Login-Button
        self.login_button = tk.Button(
            button_frame,
            text='Anmelden',
            command=self.check_password,
            font=('Arial', 12, 'bold'),
            bg=self.colors['accent'],
            fg=self.colors['fg'],
            activebackground=self.colors['accent'],
            activeforeground=self.colors['fg'],
            width=12,
            height=1,
            relief='flat',
            bd=0
        )
        self.login_button.pack()
        
        # Optionen
        options_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        options_frame.pack(pady=(20, 0), fill='x')
        
        # Passwort vergessen
        forgot_button = tk.Label(
            options_frame,
            text="Passwort vergessen?",
            font=('Arial', 9, 'underline'),
            fg=self.colors['accent'],
            bg=self.colors['bg'],
            cursor="hand2"
        )
        forgot_button.pack(side='left')
        forgot_button.bind("<Button-1>", self.forgot_password)
        
        # Hilfe
        help_button = tk.Label(
            options_frame,
            text="Hilfe",
            font=('Arial', 9, 'underline'),
            fg=self.colors['accent'],
            bg=self.colors['bg'],
            cursor="hand2"
        )
        help_button.pack(side='right')
        help_button.bind("<Button-1>", self.show_help)
        
        # Bind Enter-Taste
        self.password_entry.bind('<Return>', lambda event: self.check_password())
        
    def forgot_password(self, event=None):
        messagebox.showinfo(
            "Passwort-Erinnerung",
            "Der Standard-PIN ist: 2142\n\nBitte notieren Sie sich diesen PIN für zukünftige Anmeldungen."
        )
        
    def show_help(self, event=None):
        """Öffnet die Hilfeseite im Standard-Webbrowser"""
        help_url = 'https://maxify407578.github.io/Help-site/'
        
        try:
            webbrowser.open(help_url)
            messagebox.showinfo(
                "Hilfe wird geöffnet",
                "Die Hilfe-Seite wird in Ihrem Browser geöffnet."
            )
        except Exception as e:
            help_text = """
            Hilfe für Keylogger Pro:
            
            - Zum Starten des Loggings klicken Sie auf 'Logging starten'
            - Zum Beenden des Loggings klicken Sie auf 'Logging stoppen'
            - Logs können gespeichert oder gelöscht werden
            - Verwenden Sie die Suchfunktion, um bestimmte Einträge zu finden
            
            Bei Problemen besuchen Sie: {help_url}
            """
            messagebox.showinfo("Hilfe", help_text)
            print(f"Fehler beim Öffnen der Hilfe-Seite: {e}")
        
    def check_password(self):
        entered_password = self.password_var.get()
        
        if entered_password == self.correct_password or entered_password == self.hacker_password:
            self.status_label.config(
                text="✅ Authentifizierung erfolgreich!",
                fg=self.colors['success']
            )
            self.login_button.config(state='disabled')
            
            def start_app():
                self.root.withdraw()
                app = KeyloggerUI(self.root, hacker_mode=(entered_password == self.hacker_password))
                app.run()
            
            self.root.after(1000, start_app)
            
        else:
            self.current_attempts += 1
            remaining = self.max_attempts - self.current_attempts
            
            if remaining > 0:
                self.status_label.config(
                    text=f"❌ Falscher PIN-Code! Noch {remaining} Versuche.",
                    fg=self.colors['danger']
                )
                self.password_var.set("")
            else:
                self.status_label.config(
                    text="❌ Zu viele Fehlversuche! Programm wird beendet.",
                    fg=self.colors['danger']
                )
                self.login_button.config(state='disabled')
                self.password_entry.config(state='disabled')
                self.root.after(2000, self.root.destroy)
                
    def run(self):
        self.root.mainloop()

class KeyloggerUI:
    def __init__(self, root, hacker_mode=False):
        self.master = root
        self.root = tk.Toplevel(root)
        self.root.title('🔍 Keylogger Pro' + (' [HACKER MODE]' if hacker_mode else ''))
        self.root.geometry('900x700')
        self.root.minsize(800, 600)
        
        self.hacker_mode = hacker_mode
        if hacker_mode:
            self.colors = {
                'bg': '#0a0a0a',
                'fg': '#00ff00',
                'accent': '#008000',
                'accent_dark': '#006400',
                'success': '#00ff00',
                'danger': '#ff0000',
                'warning': '#ffff00',
                'neutral': '#808080',
                'input_bg': '#1a1a1a',
                'card_bg': '#141414'
            }
            # Hacker-Modus: Deaktiviere Schließen-Button
            self.root.protocol("WM_DELETE_WINDOW", self.block_close)
            # Deaktiviere Alt+F4
            self.root.bind('<Alt-F4>', lambda e: self.block_close())
            # Deaktiviere ESC
            self.root.bind('<Escape>', lambda e: self.block_close())
        else:
            self.colors = {
                'bg': '#1E272E',
                'fg': '#D6E0F0',
                'accent': '#3498DB',
                'accent_dark': '#2980B9',
                'success': '#2ECC71',
                'danger': '#E74C3C',
                'warning': '#F39C12',
                'neutral': '#7F8C8D',
                'input_bg': '#2C3A47',
                'card_bg': '#2C3E50'
            }
            # Normaler Modus: Erlaube normales Schließen
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Theme konfigurieren
        style = ttk.Style()
        style.theme_use('clam')
        
        # Progressbar-Stil
        style.configure(
            "TProgressbar",
            thickness=10,
            troughcolor=self.colors['bg'],
            background=self.colors['accent']
        )
        
        # Frame-Stil
        style.configure(
            'Card.TFrame', 
            background=self.colors['card_bg']
        )
        
        # Window-Stil
        self.root.configure(bg=self.colors['bg'])
        
        self.log_file = None
        self.is_logging = False
        self.key_count = 0
        self.start_time = None
        self.log_sessions = []
        
        # Zentrieren auf dem Bildschirm
        self.center_window()
        
        self.init_ui()
        
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def init_ui(self):
        # Hauptcontainer
        container = tk.Frame(self.root, bg=self.colors['bg'])
        container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(container, bg=self.colors['bg'])
        header_frame.pack(fill='x', pady=(0, 15))
        
        # Titel mit Animation
        self.title_label = tk.Label(
            header_frame,
            text='🔍 Keylogger Pro',
            font=('Arial', 28, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['bg']
        )
        self.title_label.pack(side='left')
        
        # Animiere Titel
        self.animate_title()
        
        # Status-Anzeige
        self.status_indicator = tk.Canvas(
            header_frame,
            width=20,
            height=20,
            bg=self.colors['bg'],
            highlightthickness=0
        )
        self.status_indicator.pack(side='right', padx=10)
        self.status_circle = self.status_indicator.create_oval(
            2, 2, 18, 18, 
            fill=self.colors['neutral']
        )
        
        # Status-Text
        self.status_label = tk.Label(
            header_frame,
            text='⚪ Status: Bereit',
            font=('Arial', 12, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['bg']
        )
        self.status_label.pack(side='right')
        
        # Inhalt
        content_frame = tk.Frame(container, bg=self.colors['bg'])
        content_frame.pack(fill='both', expand=True)
        
        # Linke Spalte (Karten)
        left_column = tk.Frame(content_frame, bg=self.colors['bg'], width=250)
        left_column.pack(side='left', fill='y', padx=(0, 15))
        left_column.pack_propagate(False)
        
        # Statistik-Karte
        stats_card = ttk.Frame(left_column, style='Card.TFrame')
        stats_card.pack(fill='x', pady=(0, 15), ipady=10)
        
        stats_title = tk.Label(
            stats_card,
            text='📊 Statistiken',
            font=('Arial', 14, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['card_bg']
        )
        stats_title.pack(pady=(10, 5), padx=15, anchor='w')
        
        # Statistik-Widgets
        self.key_count_label = tk.Label(
            stats_card,
            text='Tastenanschläge: 0',
            font=('Arial', 11),
            fg=self.colors['fg'],
            bg=self.colors['card_bg']
        )
        self.key_count_label.pack(pady=2, padx=15, anchor='w')
        
        self.rate_label = tk.Label(
            stats_card,
            text='Tippgeschwindigkeit: 0/min',
            font=('Arial', 11),
            fg=self.colors['fg'],
            bg=self.colors['card_bg']
        )
        self.rate_label.pack(pady=2, padx=15, anchor='w')
        
        self.time_label = tk.Label(
            stats_card,
            text='Sitzungszeit: 00:00:00',
            font=('Arial', 11),
            fg=self.colors['fg'],
            bg=self.colors['card_bg']
        )
        self.time_label.pack(pady=2, padx=15, anchor='w')
        
        self.session_label = tk.Label(
            stats_card,
            text='Aktuelle Sitzung: -',
            font=('Arial', 11),
            fg=self.colors['fg'],
            bg=self.colors['card_bg']
        )
        self.session_label.pack(pady=2, padx=15, anchor='w')
        
        # Aktivitätsanzeige
        self.activity_label = tk.Label(
            stats_card,
            text='Aktivität:',
            font=('Arial', 11),
            fg=self.colors['fg'],
            bg=self.colors['card_bg']
        )
        self.activity_label.pack(pady=(10, 2), padx=15, anchor='w')
        
        self.activity_bar = ttk.Progressbar(
            stats_card,
            orient='horizontal',
            mode='determinate',
            style="TProgressbar",
            length=220
        )
        self.activity_bar.pack(pady=2, padx=15)
        
        # Steuerungs-Karte
        control_card = ttk.Frame(left_column, style='Card.TFrame')
        control_card.pack(fill='x', ipady=10, expand=True)
        
        control_title = tk.Label(
            control_card,
            text='⚙️ Steuerung',
            font=('Arial', 14, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['card_bg']
        )
        control_title.pack(pady=(10, 15), padx=15, anchor='w')
        
        # Start/Stop Button
        self.start_button = tk.Button(
            control_card,
            text='▶️ Logging starten',
            command=self.toggle_logging,
            font=('Arial', 12, 'bold'),
            bg=self.colors['accent'],
            fg=self.colors['fg'],
            activebackground=self.colors['accent_dark'],
            activeforeground=self.colors['fg'],
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            width=20
        )
        self.start_button.pack(pady=5, padx=15)
        
        # Save Button
        self.save_button = tk.Button(
            control_card,
            text='💾 Log speichern',
            command=self.save_log_file,
            font=('Arial', 12),
            bg=self.colors['input_bg'],
            fg=self.colors['fg'],
            activebackground=self.colors['neutral'],
            activeforeground=self.colors['fg'],
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            width=20
        )
        self.save_button.pack(pady=5, padx=15)
        
        # Clear Button
        self.clear_button = tk.Button(
            control_card,
            text='🗑️ Log löschen',
            command=self.clear_log,
            font=('Arial', 12),
            bg=self.colors['input_bg'],
            fg=self.colors['fg'],
            activebackground=self.colors['neutral'],
            activeforeground=self.colors['fg'],
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            width=20
        )
        self.clear_button.pack(pady=5, padx=15)
        
        # Export Button
        self.export_button = tk.Button(
            control_card,
            text='📤 Als CSV exportieren',
            command=self.export_csv,
            font=('Arial', 12),
            bg=self.colors['input_bg'],
            fg=self.colors['fg'],
            activebackground=self.colors['neutral'],
            activeforeground=self.colors['fg'],
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            width=20
        )
        self.export_button.pack(pady=5, padx=15)
        
        # Statistik-Button hinzufügen
        stats_button = tk.Button(
            control_card,
            text='📊 Statistiken anzeigen',
            command=self.show_statistics,
            font=('Arial', 12),
            bg=self.colors['input_bg'],
            fg=self.colors['fg'],
            activebackground=self.colors['neutral'],
            activeforeground=self.colors['fg'],
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            width=20
        )
        stats_button.pack(pady=5, padx=15)
        
        # Hacker-Modus spezifische Buttons
        if self.hacker_mode:
            # Trennlinie
            separator = ttk.Separator(control_card, orient='horizontal')
            separator.pack(fill='x', pady=10, padx=15)
            
            # Hacker-Modus Label
            hacker_label = tk.Label(
                control_card,
                text='🔒 HACKER MODE AKTIV',
                font=('Arial', 12, 'bold'),
                fg=self.colors['warning'],
                bg=self.colors['card_bg']
            )
            hacker_label.pack(pady=5)
            
            # Stealth Mode Button
            self.stealth_button = tk.Button(
                control_card,
                text='👻 Stealth Mode',
                command=self.toggle_stealth_mode,
                font=('Arial', 12),
                bg=self.colors['input_bg'],
                fg=self.colors['fg'],
                activebackground=self.colors['neutral'],
                activeforeground=self.colors['fg'],
                relief='flat',
                bd=0,
                padx=15,
                pady=8,
                width=20
            )
            self.stealth_button.pack(pady=5, padx=15)
            
            # Screenshot Button
            self.screenshot_button = tk.Button(
                control_card,
                text='📸 Screenshot',
                command=self.take_screenshot,
                font=('Arial', 12),
                bg=self.colors['input_bg'],
                fg=self.colors['fg'],
                activebackground=self.colors['neutral'],
                activeforeground=self.colors['fg'],
                relief='flat',
                bd=0,
                padx=15,
                pady=8,
                width=20
            )
            self.screenshot_button.pack(pady=5, padx=15)
        
        # Rechte Spalte (Log-Anzeige)
        right_column = tk.Frame(content_frame, bg=self.colors['bg'])
        right_column.pack(side='right', fill='both', expand=True)
        
        # Log-Header
        log_header = tk.Frame(right_column, bg=self.colors['bg'])
        log_header.pack(fill='x', pady=(0, 10))
        
        log_title = tk.Label(
            log_header,
            text='📝 Aufzeichnung',
            font=('Arial', 14, 'bold'),
            fg=self.colors['fg'],
            bg=self.colors['bg']
        )
        log_title.pack(side='left')
        
        # Suchen-Label
        search_frame = tk.Frame(log_header, bg=self.colors['bg'])
        search_frame.pack(side='right')
        
        search_label = tk.Label(
            search_frame,
            text='🔍 Suchen:',
            font=('Arial', 11),
            fg=self.colors['fg'],
            bg=self.colors['bg']
        )
        search_label.pack(side='left', padx=(0, 5))
        
        # Suchen-Eingabe
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.search_logs)
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=('Arial', 11),
            bg=self.colors['input_bg'],
            fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            width=15
        )
        search_entry.pack(side='right')
        
        # Log-Anzeige
        self.log_display = scrolledtext.ScrolledText(
            right_column,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg=self.colors['input_bg'],
            fg=self.colors['fg'],
            insertbackground=self.colors['fg']
        )
        self.log_display.pack(fill='both', expand=True)
        self.log_display.config(state='disabled')
        
        # Hover-Effekte für Buttons
        for button in [self.start_button, self.save_button, self.clear_button, self.export_button]:
            button.bind('<Enter>', lambda e, b=button: self.on_button_hover(e, b))
            button.bind('<Leave>', lambda e, b=button: self.on_button_leave(e, b))
        
        # Footer
        footer_frame = tk.Frame(container, bg=self.colors['bg'], height=30)
        footer_frame.pack(fill='x', pady=(15, 0))
        
        footer_text = tk.Label(
            footer_frame,
            text='© 2024 Keylogger Pro • Letzte Aktivität: -',
            font=('Arial', 9),
            fg=self.colors['neutral'],
            bg=self.colors['bg']
        )
        footer_text.pack(side='left')
        
        # Tastendruck-Event binden
        self.root.bind('<Key>', self.on_key_press)
        
        # Schließen-Event binden
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Statistik-Timer
        self.stats_timer = threading.Thread(target=self.update_stats_loop)
        self.stats_timer.daemon = True
        self.stats_timer.start()
        
    def animate_title(self):
        def animation():
            colors = [self.colors['accent'], self.colors['accent_dark']]
            while True:
                for color in colors:
                    try:
                        self.title_label.config(fg=color)
                        time.sleep(1.0)  # Längere Pause für weniger CPU-Last
                    except:
                        return
        
        threading.Thread(target=animation, daemon=True).start()
        
    def update_stats_loop(self):
        while True:
            if self.is_logging and self.start_time:
                try:
                    elapsed = datetime.now() - self.start_time
                    hours, remainder = divmod(elapsed.total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    # Batch-Update der UI-Elemente
                    def update_ui():
                        time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                        self.time_label.config(text=f'Sitzungszeit: {time_str}')
                        
                        if elapsed.total_seconds() > 0:
                            rate = (self.key_count / elapsed.total_seconds()) * 60
                            self.rate_label.config(text=f'Tippgeschwindigkeit: {rate:.1f}/min')
                            activity = min(100, int(rate * 2))
                            self.activity_bar['value'] = activity
                    
                    self.root.after(0, update_ui)
                except:
                    pass
            time.sleep(0.5)  # Häufigere Updates aber weniger UI-Updates
        
    def on_button_hover(self, event, button):
        if button == self.start_button:
            if self.is_logging:
                button.configure(bg='#C0392B')  # Dunkleres Rot wenn aktiv
            else:
                button.configure(bg=self.colors['accent_dark'])
        else:
            button.configure(bg=self.colors['neutral'])
            
    def on_button_leave(self, event, button):
        if button == self.start_button:
            if self.is_logging:
                button.configure(bg=self.colors['danger'])
            else:
                button.configure(bg=self.colors['accent'])
        else:
            button.configure(bg=self.colors['input_bg'])
        
    def toggle_logging(self):
        if not self.is_logging:
            self.start_logging()
        else:
            self.stop_logging()
            
    def start_logging(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"keylog_{timestamp}.txt"
        self.log_file = open(filename, "a")
        self.log_file.write(f"=== Keylogger-Sitzung gestartet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
        
        self.is_logging = True
        self.start_time = datetime.now()
        self.session_label.config(text=f'Aktuelle Sitzung: {timestamp}')
        
        # Status aktualisieren
        self.status_label.config(
            text='🟢 Status: Aktiv',
            fg=self.colors['success']
        )
        self.status_indicator.itemconfig(
            self.status_circle, 
            fill=self.colors['success']
        )
        
        # Button aktualisieren
        self.start_button.config(
            text='⏹️ Logging stoppen',
            bg=self.colors['danger']
        )
        
        # Animation
        self.animate_logging_start()
        
    def stop_logging(self):
        if self.log_file:
            self.log_file.write(f"\n=== Keylogger-Sitzung beendet: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            self.log_file.write(f"=== Insgesamt {self.key_count} Tastenanschläge aufgezeichnet ===\n")
            self.log_file.close()
            
        self.is_logging = False
        session_time = datetime.now() - self.start_time
        
        # Sitzung zur Historie hinzufügen
        self.log_sessions.append({
            'start': self.start_time,
            'end': datetime.now(),
            'duration': session_time,
            'key_count': self.key_count
        })
        
        # Status aktualisieren
        self.status_label.config(
            text='⚪ Status: Bereit',
            fg=self.colors['fg']
        )
        self.status_indicator.itemconfig(
            self.status_circle, 
            fill=self.colors['neutral']
        )
        
        # Button aktualisieren
        self.start_button.config(
            text='▶️ Logging starten',
            bg=self.colors['accent']
        )
        
        # Animation
        self.animate_logging_stop()
        
    def animate_logging_start(self):
        def animation():
            self.status_indicator.itemconfig(self.status_circle, width=0)
            self.status_indicator.itemconfig(
                self.status_circle,
                outline=self.colors['success'],
                width=2
            )
        
        self.root.after(0, animation)
        
    def animate_logging_stop(self):
        def animation():
            self.status_indicator.itemconfig(
                self.status_circle,
                outline='',
                width=0,
                fill=self.colors['neutral']
            )
        
        self.root.after(0, animation)
        
    def clear_log(self):
        if messagebox.askyesno(
            '🗑️ Log löschen',
            'Möchten Sie wirklich alle Logs löschen?',
            icon='warning'
        ):
            self.log_display.config(state='normal')
            self.log_display.delete('1.0', tk.END)
            self.log_display.config(state='disabled')
            
            # Stats zurücksetzen
            self.key_count = 0
            self.key_count_label.config(text=f'Tastenanschläge: {self.key_count}')
            self.rate_label.config(text='Tippgeschwindigkeit: 0/min')
            self.activity_bar['value'] = 0
        
    def save_log_file(self):
        log_text = self.log_display.get('1.0', tk.END).strip()
        if not log_text:
            messagebox.showwarning(
                '⚠️ Warnung',
                'Keine Logs zum Speichern vorhanden!'
            )
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"keylog_saved_{timestamp}.txt"
            
            with open(filename, 'w') as file:
                file.write(log_text)
            
            messagebox.showinfo(
                '✅ Erfolg',
                f'Log wurde gespeichert als:\n{filename}'
            )
            
        except Exception as e:
            messagebox.showerror(
                '❌ Fehler',
                f'Fehler beim Speichern: {e}'
            )
            
    def export_csv(self):
        log_text = self.log_display.get('1.0', tk.END).strip()
        if not log_text:
            messagebox.showwarning(
                '⚠️ Warnung',
                'Keine Logs zum Exportieren vorhanden!'
            )
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"keylog_export_{timestamp}.csv"
            
            with open(filename, 'w') as file:
                file.write("Zeitstempel,Ereignis,Taste\n")
                
                for line in log_text.split('\n'):
                    if "Taste gedrückt" in line and ":" in line:
                        parts = line.split(': ', 1)
                        if len(parts) == 2:
                            time_part = parts[0]
                            event_part = parts[1]
                            
                            # Extrahieren des Tastennamens
                            key_name = event_part.replace("Taste gedrückt - ", "")
                            
                            file.write(f'"{time_part}","Taste gedrückt","{key_name}"\n')
            
            messagebox.showinfo(
                '✅ Erfolg',
                f'Log wurde als CSV exportiert:\n{filename}'
            )
            
        except Exception as e:
            messagebox.showerror(
                '❌ Fehler',
                f'Fehler beim Exportieren: {e}'
            )
            
    def search_logs(self, *args):
        search_text = self.search_var.get().lower()
        if not search_text:
            return
            
        content = self.log_display.get('1.0', tk.END)
        self.log_display.tag_remove('search', '1.0', tk.END)
        
        start_pos = '1.0'
        while True:
            start_pos = self.log_display.search(
                search_text, start_pos, tk.END, nocase=True
            )
            if not start_pos:
                break
                
            end_pos = f"{start_pos}+{len(search_text)}c"
            self.log_display.tag_add('search', start_pos, end_pos)
            start_pos = end_pos
            
        self.log_display.tag_config('search', background='#F39C12', foreground='black')
            
    def append_to_log(self, text):
        self.log_display.config(state='normal')
        self.log_display.insert(tk.END, text + '\n')
        self.log_display.see(tk.END)
        self.log_display.config(state='disabled')
        self.search_logs()  # Aktualisiere Suche
        
    def on_key_press(self, event):
        if self.is_logging:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            key = event.char or event.keysym
            
            # Erweiterte Logging im Hacker-Modus
            if self.hacker_mode:
                # Aktives Fenster ermitteln
                try:
                    from win32gui import GetWindowText, GetForegroundWindow
                    window = GetWindowText(GetForegroundWindow())
                except ImportError:
                    try:
                        import win32gui
                        window = win32gui.GetWindowText(win32gui.GetForegroundWindow())
                    except:
                        window = "Unbekannt"
                except:
                    window = "Unbekannt"
                
                log_text = f"{timestamp}: [{window}] Taste gedrückt - {key}"
            else:
                log_text = f"{timestamp}: Taste gedrückt - {key}"
                
            self.append_to_log(log_text)
            
            if self.log_file:
                self.log_file.write(log_text + '\n')
                self.log_file.flush()
                
            self.key_count += 1
            self.key_count_label.config(text=f'Tastenanschläge: {self.key_count}')
            
    def on_closing(self):
        if self.is_logging:
            if messagebox.askyesno(
                '❓ Beenden',
                'Das Logging läuft noch. Möchten Sie wirklich beenden?',
                icon='warning'
            ):
                self.stop_logging()
                self.root.destroy()
                self.master.destroy()  # Auch das Hauptfenster schließen
        else:
            self.root.destroy()
            self.master.destroy()  # Auch das Hauptfenster schließen
        
    def run(self):
        # Keine mainloop hier, da wir bereits eine im Login-Fenster haben
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.deiconify()  # Zeige das Fenster an
        
    def show_statistics(self):
        StatisticsWindow(self.root, self.log_sessions, self.key_count)

    def block_close(self):
        messagebox.showwarning(
            '🔒 Hacker Mode',
            'Im Hacker-Modus kann das Programm nur über den Task-Manager beendet werden!\n\nStrg+Alt+Entf → Task-Manager → Prozess beenden',
            icon='warning'
        )
        return 'break'

    def toggle_stealth_mode(self):
        if not hasattr(self, 'stealth_mode'):
            self.stealth_mode = False
        
        self.stealth_mode = not self.stealth_mode
        
        if self.stealth_mode:
            # Verstecke Fenster aus Taskleiste
            self.root.withdraw()
            self.stealth_button.config(
                text='👻 Stealth Mode (Aktiv)',
                bg=self.colors['success']
            )
            # Erstelle System-Tray-Icon
            self.show_notification(
                'Stealth Mode aktiviert',
                'Keylogger läuft im Hintergrund.\nStrg+Alt+H zum Anzeigen'
            )
            # Hotkey zum Anzeigen
            self.root.bind_all('<Control-Alt-h>', lambda e: self.show_window())
        else:
            self.root.deiconify()
            self.stealth_button.config(
                text='👻 Stealth Mode',
                bg=self.colors['input_bg']
            )
            self.show_notification(
                'Stealth Mode deaktiviert',
                'Keylogger ist wieder sichtbar'
            )

    def show_window(self):
        if hasattr(self, 'stealth_mode') and self.stealth_mode:
            self.root.deiconify()
            self.stealth_mode = False
            self.stealth_button.config(
                text='👻 Stealth Mode',
                bg=self.colors['input_bg']
            )

    def take_screenshot(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            
            # Screenshot aufnehmen
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            
            # Log-Eintrag
            log_text = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Screenshot gespeichert als {filename}"
            self.append_to_log(log_text)
            
            self.show_notification(
                'Screenshot erstellt',
                f'Gespeichert als: {filename}'
            )
            
        except Exception as e:
            messagebox.showerror(
                '❌ Fehler',
                f'Fehler beim Screenshot: {e}'
            )

    def show_notification(self, title, message):
        if self.hacker_mode:
            # Zeige Desktop-Benachrichtigung
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(
                    title,
                    message,
                    duration=3,
                    threaded=True
                )
            except:
                # Fallback wenn win10toast nicht verfügbar
                messagebox.showinfo(title, message)

@app.route('/purchase', methods=['POST'])
def purchase():
    data = request.get_json()
    plan = data.get('plan')
    price = data.get('price')
    name = data.get('name')
    email = data.get('email')
    key = data.get('key')  # Schlüssel aus den Daten extrahieren

    # Hier kannst du den Schlüssel speichern oder verwenden
    print(f"Neuer Kauf: {plan}, Preis: {price}, Name: {name}, E-Mail: {email}, Schlüssel: {key}")

    # Hier kannst du die Logik für die Speicherung des Schlüssels hinzufügen
    # Zum Beispiel in einer Datei oder Datenbank

    return jsonify({"message": "Kauf erfolgreich!"}), 200

def is_port_available(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            return True
    except:
        return False

def find_free_port():
    port = SERVER_PORT
    while not is_port_available(port) and port < SERVER_PORT + 100:
        port += 1
    return port

def start_server():
    try:
        port = find_free_port()
        Handler = CustomHandler
        
        # Setze den Server auf "allow_reuse_address", um "Address already in use" zu vermeiden
        socketserver.TCPServer.allow_reuse_address = True
        
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"Server läuft auf Port {port}")
            global SERVER_PORT
            SERVER_PORT = port
            httpd.serve_forever()
    except Exception as e:
        print(f"Server-Fehler: {e}")
        messagebox.showerror("Server-Fehler", f"Konnte Server nicht starten: {e}")

def open_payment_page():
    try:
        # Warte kurz, damit der Server Zeit hat zu starten
        time.sleep(2)
        url = f'http://localhost:{SERVER_PORT}/pay.html'
        print(f"Öffne: {url}")
        webbrowser.open(url)
    except Exception as e:
        print(f"Fehler beim Öffnen der Bezahlseite: {e}")
        messagebox.showerror("Fehler", f"Konnte Bezahlseite nicht öffnen: {e}")

def main():
    """Startet die Anwendung und den Server."""
    try:
        # Prüfe ob pay.html existiert
        if not os.path.exists('pay.html'):
            messagebox.showerror("Fehler", "pay.html wurde nicht gefunden!")
            return
            
        # Starte den Server in einem separaten Thread
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Öffne die Bezahlseite
        payment_thread = threading.Thread(target=open_payment_page)
        payment_thread.start()
        
        # Starte die Hauptanwendung
        login = LoginWindow()
        login.run()
        
    except Exception as e:
        messagebox.showerror("Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {e}")

if __name__ == '__main__':
    main()