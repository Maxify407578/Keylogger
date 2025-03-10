# 🔍 Keylogger Pro - Webshop

Ein moderner Webshop für den Keylogger Pro mit sicherer Zahlungsabwicklung.

## 📋 Funktionen

- Responsive Design
- Drei Preispläne (Basic, Professional, Enterprise)
- Sichere Zahlungsabwicklung
- Kartenvalidierung in Echtzeit
- Terminal-Benachrichtigungen für neue Käufe
- **Hacker-Modus** für erweiterte Funktionen (z.B. Screenshots)

## 🚀 Installation

1. Stelle sicher, dass [Node.js](https://nodejs.org/) installiert ist.
2. Klone das Repository:
    ```bash
    git clone https://github.com/dein-username/keylogger-pro-shop.git
    cd keylogger-pro-shop
    ```
3. Installiere die Abhängigkeiten:
    ```bash
    npm install
    ```

## 💻 Verwendung

1. Starte den Server:
    ```bash
    npm start
    ```
2. Öffne im Browser:
    ```
    http://localhost:3000
    ```

## 📦 Projektstruktur

```

## 🔧 Technologien

- Frontend:
  - HTML5
  - CSS3 (Custom Properties, Flexbox, Grid)
  - Vanilla JavaScript
  - Responsive Design

- Backend:
  - Node.js
  - Express.js
  - CORS

## 💳 Zahlungsabwicklung

Der Shop unterstützt folgende Zahlungsmethoden:
- Visa
- Mastercard
- PayPal

Alle Zahlungsdaten werden sicher verarbeitet:
- Nur die letzten 4 Ziffern der Karte werden gespeichert
- SSL-Verschlüsselung
- Validierung auf Client- und Serverseite

## 📊 Monitoring

Alle Käufe werden im Terminal angezeigt mit:
- Gewählter Plan
- Preis
- Kundendaten
- Zeitstempel
- Maskierte Kartendaten

## 🔒 Sicherheit

- CORS-Schutz
- Eingabevalidierung
- Sichere Kartenverarbeitung
- Keine Speicherung sensibler Daten

## 🛠️ Development

Für die Entwicklung mit automatischem Neuladen:
```bash
npm run dev
```

## 📝 Umgebungsvariablen

Der Server läuft standardmäßig auf Port 3000. Dies kann in der `server.js` angepasst werden.

## ⚠️ Wichtige Hinweise

- Dies ist eine Demo-Version
- Keine echten Zahlungen werden verarbeitet
- Nur für Testzwecke verwenden

## 📄 Lizenz

Alle Rechte vorbehalten. © 2024 Keylogger Pro