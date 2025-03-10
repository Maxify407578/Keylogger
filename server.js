const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const port = 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Serviere Pay.html als Hauptseite
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'Pay.html'));
});

// Kaufanfragen-Handler
app.post('/purchase', (req, res) => {
    try {
        const purchaseData = req.body;
        
        // Log im Terminal
        console.log('\n=== NEUE KAUFANFRAGE ===');
        console.log('Plan:', purchaseData.plan);
        console.log('Preis:', purchaseData.price);
        console.log('Name:', purchaseData.name);
        console.log('Email:', purchaseData.email);
        console.log('Karte:', '**** **** **** ' + purchaseData.cardInfo.lastFour);
        console.log('========================\n');

        // Erfolgsantwort
        res.json({ status: 'success' });
    } catch (error) {
        console.error('Fehler:', error);
        res.status(500).json({ status: 'error' });
    }
});

// Server starten
app.listen(port, () => {
    console.log(`Server läuft auf http://localhost:${port}`);
}); 