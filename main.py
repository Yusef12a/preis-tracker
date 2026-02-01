#!/usr/bin/env python3
"""
🤖 SERVERLESS PREIS-TRACKER
Überwacht Produktpreise und benachrichtigt dich bei Änderungen via Telegram
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from supabase import create_client
from datetime import datetime
import re

# ============================================
# KONFIGURATION
# ============================================

# Umgebungsvariablen (werden von GitHub Actions gesetzt)
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Produkte die getrackt werden sollen
# WICHTIG: Hier deine eigenen Produkte eintragen!
PRODUCTS = [
    {
        'name': 'PlayStation 5',
        'url': 'https://www.amazon.de/Playstation%C2%AE5-Digital-Edition-825-GB/dp/B0FN7ZG39D/ref=sr_1_3?__mk_de_DE=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=673V2WF6HNSM&dib=eyJ2IjoiMSJ9.Zd2DXQU-z94EU57vri9gcuuLmliL1AeNE91RL4TTyfzuJa3vj2g1jfowwwIkKZpz57kW91RMKa7_9hDuDLapQnV5N_HznK8B24ocggwCc3K3poYZc90KtGJCzaVwVOz2rweW2knTwDWy25e-WGOvnKzRkIauFW26-tE0PxpM3P4Wdhnifd2CyCDvzxFG0TmRZ5sbb_VQuNZiaFnsij4TJ2OgCtLOnHStwYvKfu9wnjQ.we58TqI_42vBiIxRCyxSZxIMn0_ge2oOSHZ6rlRMvRY&dib_tag=se&keywords=PlayStation+5&qid=1769940274&sprefix=playstation+5%2Caps%2C171&sr=8-3'
    },
    {
        'name': 'Apple AirPods Pro',
        'url': 'https://www.amazon.de/Apple-Kabellose-Ger%C3%A4uschunterdr%C3%BCckung-Herzfrequenzmessung-H%C3%B6rger%C3%A4tefunktion/dp/B0FQF32239/ref=sr_1_4?__mk_de_DE=%C3%85M%C3%85%C5%BD%C3%95%C3%91&crid=2EEPBMH68U6NZ&dib=eyJ2IjoiMSJ9.Z_pcgt2KKWTUeTV1dd-iZS61LreeKf-APdy4AylqTrm7fEVJPnv3Oqe4-2INhmJIro9jhW5oyLzXkKjEErSlLXJc-RSmO58ipU2vd3PDTodpjkNRDIwUOxoWpcly6hNVGk7U5HIXw-eUdaPmsbG9BeCcMyDun-bXnaELNEWiau8khgo4AvGTwLX48QNp_m8x0hwZxD90UWcIlV_L1zu-Sz25V2BQOcBMKOUUVSdgt8U.NIEGNx_SD9x8E9PNzKLckAF5eRYTX9tNFnr6VPQpWFE&dib_tag=se&keywords=Apple+AirPods+Pro&qid=1769940315&sprefix=apple+airpods+pro%2Caps%2C178&sr=8-4'
    },
    # Füge weitere Produkte hinzu (einfach kopieren und anpassen)
]

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# ============================================
# FUNKTIONEN
# ============================================

def send_telegram(message):
    """Sendet eine Telegram-Nachricht"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data)
        return response.ok
    except Exception as e:
        print(f"❌ Telegram-Fehler: {e}")
        return False

def extract_price(text):
    """Extrahiert Preis aus Text (z.B. '499,99 €' → 499.99)"""
    try:
        # Entferne alles außer Zahlen, Komma und Punkt
        clean = re.sub(r'[^\d,.]', '', text)
        # Ersetze Komma durch Punkt
        clean = clean.replace(',', '.')
        return float(clean)
    except:
        return None

def scrape_amazon_price(url):
    """Scrapt Preis von Amazon"""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Amazon hat verschiedene Preis-Selektoren
        selectors = [
            'span.a-price-whole',
            'span.a-offscreen',
            'span#priceblock_ourprice',
            'span#priceblock_dealprice',
            'span.a-price span.a-offscreen'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                price = extract_price(element.get_text())
                if price and price > 0:
                    return price
        
        return None
    except Exception as e:
        print(f"❌ Scraping-Fehler: {e}")
        return None

def check_prices():
    """Hauptfunktion: Prüft alle Preise und sendet Benachrichtigungen"""
    print("🚀 Starte Preis-Check...")
    print(f"⏰ Zeit: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("="*50)
    
    # Verbinde mit Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    checked = 0
    price_drops = 0
    errors = 0
    
    for product in PRODUCTS:
        name = product['name']
        url = product['url']
        
        print(f"\n📦 {name}")
        print(f"   🔗 {url[:50]}...")
        
        # Scrape aktuellen Preis
        current_price = scrape_amazon_price(url)
        
        if current_price is None:
            print(f"   ⚠️  Preis konnte nicht ermittelt werden")
            errors += 1
            continue
        
        print(f"   💰 Aktueller Preis: {current_price:.2f} €")
        checked += 1
        
        # Hole Produkt aus Datenbank
        try:
            result = supabase.table('products').select('*').eq('url', url).execute()
            
            if result.data:
                # Produkt existiert bereits
                product_data = result.data[0]
                product_id = product_data['id']
                old_price = float(product_data['current_price'])
                lowest_price = float(product_data['lowest_price'])
                
                # Prüfe auf Preisänderung
                if current_price < old_price:
                    # PREISSENKUNG! 🎉
                    discount = old_price - current_price
                    discount_percent = (discount / old_price) * 100
                    
                    print(f"   📉 PREISSENKUNG: {old_price:.2f} € → {current_price:.2f} € (-{discount_percent:.1f}%)")
                    price_drops += 1
                    
                    # Sende Telegram-Benachrichtigung
                    message = f"""
🔔 <b>PREISALARM!</b> 🔔

📦 <b>{name}</b>

💰 Vorher: {old_price:.2f} €
✅ Jetzt: {current_price:.2f} €
📉 Ersparnis: {discount:.2f} € ({discount_percent:.1f}%)

🔗 <a href="{url}">Zum Produkt</a>
"""
                    send_telegram(message)
                    
                    # Prüfe auf neuen Tiefstpreis
                    if current_price < lowest_price:
                        print(f"   🎉 NEUER TIEFSTPREIS!")
                        lowest_message = f"""
🏆 <b>NEUER TIEFSTPREIS!</b> 🏆

📦 <b>{name}</b>
💎 Bester Preis ever: {current_price:.2f} €

🔗 <a href="{url}">Jetzt zuschlagen!</a>
"""
                        send_telegram(lowest_message)
                
                elif current_price > old_price:
                    print(f"   📈 Preis gestiegen: {old_price:.2f} € → {current_price:.2f} €")
                else:
                    print(f"   ➡️  Preis unverändert")
                
                # Update Produkt in DB
                update_data = {
                    'current_price': current_price,
                    'lowest_price': min(current_price, lowest_price),
                    'last_checked': datetime.now().isoformat()
                }
                supabase.table('products').update(update_data).eq('id', product_id).execute()
                
                # Füge zu Historie hinzu
                supabase.table('price_history').insert({
                    'product_id': product_id,
                    'price': current_price
                }).execute()
                
            else:
                # Neues Produkt - erstelle Eintrag
                print(f"   ✨ Neues Produkt wird getrackt")
                new_product = {
                    'url': url,
                    'name': name,
                    'current_price': current_price,
                    'lowest_price': current_price
                }
                result = supabase.table('products').insert(new_product).execute()
                
                # Sende Info
                message = f"""
✅ <b>Neues Produkt wird überwacht</b>

📦 {name}
💰 Startpreis: {current_price:.2f} €

Ich benachrichtige dich bei Preisänderungen!
"""
                send_telegram(message)
                
        except Exception as e:
            print(f"   ❌ Datenbankfehler: {e}")
            errors += 1
    
    # Zusammenfassung
    print("\n" + "="*50)
    print(f"✅ Check abgeschlossen!")
    print(f"   📊 Produkte geprüft: {checked}")
    print(f"   📉 Preissenkungen: {price_drops}")
    print(f"   ❌ Fehler: {errors}")
    
    # Sende Zusammenfassung (nur wenn Preissenkungen)
    if price_drops > 0:
        summary = f"""
📊 <b>Preis-Check abgeschlossen</b>

✅ {checked} Produkte geprüft
📉 {price_drops} Preissenkung{'en' if price_drops != 1 else ''}
"""
        send_telegram(summary)

# ============================================
# HAUPTPROGRAMM
# ============================================

if __name__ == '__main__':
    try:
        check_prices()
    except Exception as e:
        print(f"❌ KRITISCHER FEHLER: {e}")
        send_telegram(f"⚠️ <b>Fehler beim Preis-Check:</b>\n\n{str(e)}")
        sys.exit(1)
