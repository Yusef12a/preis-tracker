# 🤖 Serverless Preis-Tracker

Ein vollautomatischer Preis-Tracker, der **komplett kostenlos** läuft und dich per Telegram benachrichtigt, wenn Produkte günstiger werden!

## 🎯 Features

- ✅ **Komplett kostenlos** (nutzt nur Free-Tier Services)
- 🔄 **Automatisch alle 6 Stunden** prüfen
- 📱 **Telegram-Benachrichtigungen** bei Preissenkungen
- 💾 **Preis-Historie** in Supabase-Datenbank
- 🎉 **Neuer Tiefstpreis**-Alarme
- 🛒 Unterstützt **Amazon** und andere Shops

## 📋 Voraussetzungen

- GitHub Account (kostenlos)
- Telegram Account (kostenlos)
- Supabase Account (kostenlos)

## 🚀 Setup-Anleitung

### 1. Telegram Bot erstellen

1. Öffne Telegram und suche **@BotFather**
2. Sende `/newbot` und folge den Anweisungen
3. **Kopiere den Bot Token** (z.B. `1234567890:ABC...`)
4. Starte deinen Bot mit `/start`
5. Finde deine Chat ID:
   - Öffne: `https://api.telegram.org/bot<DEIN_TOKEN>/getUpdates`
   - Kopiere die Zahl bei `"id"`

### 2. Supabase Datenbank einrichten

1. Gehe zu [supabase.com](https://supabase.com) und erstelle einen Account
2. Erstelle ein neues Projekt: `preis-tracker`
3. Gehe zu **SQL Editor** und führe aus:

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    current_price DECIMAL(10,2),
    lowest_price DECIMAL(10,2),
    last_checked TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    price DECIMAL(10,2),
    checked_at TIMESTAMP DEFAULT NOW()
);
```

4. Kopiere aus **Settings → API**:
   - Project URL
   - anon/public Key

### 3. GitHub Repository einrichten

1. **Forke** dieses Repository oder erstelle ein neues
2. Lade alle Dateien hoch
3. Gehe zu **Settings → Secrets → Actions**
4. Füge diese **4 Secrets** hinzu:

| Name | Wert |
|------|------|
| `SUPABASE_URL` | Deine Supabase URL |
| `SUPABASE_KEY` | Dein Supabase API Key |
| `TELEGRAM_BOT_TOKEN` | Dein Bot Token |
| `TELEGRAM_CHAT_ID` | Deine Chat ID |

### 4. Produkte hinzufügen

Bearbeite `main.py` und füge deine Produkte hinzu:

```python
PRODUCTS = [
    {
        'name': 'PlayStation 5',
        'url': 'https://www.amazon.de/dp/PRODUKTID'
    },
    {
        'name': 'Apple AirPods',
        'url': 'https://www.amazon.de/dp/PRODUKTID'
    },
]
```

### 5. Workflow aktivieren

1. Gehe zu **Actions** in deinem Repository
2. Aktiviere Workflows (falls nötig)
3. Klicke auf **"Preis-Tracker"** → **"Run workflow"**
4. Der erste Check startet sofort!

## 📊 Wie es funktioniert

```
┌─────────────────────────────────────────┐
│  GitHub Actions (alle 6 Stunden)       │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Python Script scrapt Preise           │
│  • Amazon.de                            │
│  • Weitere Shops möglich                │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Supabase Datenbank                     │
│  • Speichert Preise                     │
│  • Vergleicht mit Historie              │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Telegram Benachrichtigung              │
│  🔔 Preissenkung gefunden!              │
└─────────────────────────────────────────┘
```

## 🎛️ Anpassungen

### Zeitplan ändern

Bearbeite `.github/workflows/price-check.yml`:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Alle 6 Stunden
  # - cron: '0 */3 * * *'  # Alle 3 Stunden
  # - cron: '0 8,20 * * *'  # Um 8:00 und 20:00 Uhr
```

### Weitere Shops hinzufügen

Erweitere die `scrape_amazon_price()` Funktion oder füge neue Funktionen hinzu.

## 🐛 Fehlersuche

**Keine Benachrichtigungen?**
- Prüfe ob Secrets richtig gesetzt sind
- Teste den Bot: Schreibe ihm in Telegram
- Prüfe GitHub Actions Log

**Preis nicht gefunden?**
- Amazon ändert manchmal HTML-Struktur
- Probiere andere Produkt-URLs
- Prüfe ob Produkt verfügbar ist

**Workflow läuft nicht?**
- Actions müssen aktiviert sein
- Repository muss Aktivität haben (commit etwas)

## 📈 Erweiterungen

Ideen für weitere Features:
- 📧 E-Mail-Benachrichtigungen
- 🎨 Web-Dashboard mit Vercel
- 📊 Preis-Diagramme
- 🔔 Discord-Integration
- 🌍 Mehrere Amazon-Länder
- 🤖 ChatGPT-Integration für Empfehlungen

## 💡 Kosten

**Komplett kostenlos!** 🎉

- GitHub Actions: 2.000 Minuten/Monat (1 Check = ~1 Minute)
- Supabase: 500 MB Datenbank (reicht für 1000+ Produkte)
- Telegram: Unbegrenzt kostenlos

## 📝 Lizenz

MIT License - nutze es wie du willst!

## 🤝 Beitragen

Pull Requests sind willkommen! Ideen:
- Weitere Shops unterstützen
- Besseres Error-Handling
- Web-Interface

---

**Made with ❤️ for saving money!**

Fragen? Öffne ein Issue!
