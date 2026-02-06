#!/usr/bin/env python3
"""
🤖 SERVERLESS PREIS-TRACKER - VERBESSERTE VERSION
Überwacht Produktpreise und benachrichtigt dich bei Änderungen via Telegram
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from supabase import create_client
from datetime import datetime
import re
import time

# ============================================
# KONFIGURATION
# ============================================

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# WICHTIG: Nur einfache Amazon-URLs verwenden (ohne % Zeichen)
PRODUCTS = [
    {
        'name': 'Apple AirPods Pro 2',
        'url': 'https://www.otto.de/p/share/w/2029107354'
    },
    {
        'name': 'PlayStation 5 Slim',
        'url': 'https://www.otto.de/p/share/w/1802445948'
    },
    {
        'name': 'WF-C700N wireless In-Ear-Kopfhörer',
        'url': 'https://www.otto.de/p/share/w/1729365106'
    },
    # Füge weitere Produkte hinzu - WICHTIG: Format muss sein: /dp/PRODUKTID
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

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
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        response = requests.post(url, data=data, timeout=10)
        return response.ok
    except Exception as e:
        print(f"❌ Telegram-Fehler: {e}")
        return False

def extract_price(text):
    """Extrahiert Preis aus Text (z.B. '499,99 €' → 499.99)"""
    try:
        # Entferne Leerzeichen
        text = text.replace(' ', '')
        # Finde Muster wie 499,99 oder 499.99
        match = re.search(r'(\d+)[,.](\d{2})', text)
        if match:
            return float(f"{match.group(1)}.{match.group(2)}")
        return None
    except:
        return None

def scrape_amazon_price(url):
    """Scrapt Preis von Amazon - VERBESSERTE VERSION"""
    try:
        # Verschiedene User Agents probieren
        for user_agent in USER_AGENTS:
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            try:
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    print(f"   ⚠️  HTTP Status: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # METHODE 1: Preis-Klassen (am zuverlässigsten)
                price_selectors = [
                    # Amazon Selektoren
                    '.a-price .a-offscreen',
                    'span.a-price-whole',
                    '.a-price-whole',
                    # OTTO Selektoren (Neu hinzugefügt)
                    '.p_price__inner', 
                    '#pd_price',
                    '.js_purchasePrice',
                    'span[itemprop="price"]',
                     # Allgemeine Selektoren
                    '.price',
                    '[data-qa="product-price"]'
                    ]
                
                for selector in price_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        price_text = element.get_text()
                        price = extract_price(price_text)
                        if price and price > 0 and price < 10000:
                            print(f"   ✅ Preis gefunden mit Methode: {selector}")
                            return price
                
                # METHODE 2: Suche im gesamten HTML nach Preis-Pattern
                text = soup.get_text()
                # Suche nach "EUR 499,99" oder "€ 499,99" Pattern
                patterns = [
                    r'EUR\s*(\d+)[,.](\d{2})',
                    r'€\s*(\d+)[,.](\d{2})',
                    r'(\d+)[,.](\d{2})\s*€',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        # Nimm den ersten realistischen Preis
                        for match in matches:
                            if isinstance(match, tuple):
                                price = float(f"{match[0]}.{match[1]}")
                            else:
                                price = extract_price(match)
                            
                            if price and 1 < price < 10000:
                                print(f"   ✅ Preis gefunden mit Pattern-Suche")
                                return price
                
                # Wenn dieser User-Agent nicht funktioniert, nächsten probieren
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️  Request-Fehler mit User-Agent {user_agent[:50]}...")
                continue
        
        return None
            
    except Exception as e:
        print(f"   ❌ Scraping-Fehler: {e}")
        return None

def check_prices():
    """Hauptfunktion: Prüft alle Preise und sendet Benachrichtigungen"""
    print("🚀 Starte Preis-Check...")
    print(f"⏰ Zeit: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("="*50)
    
    # Verbinde mit Supabase
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"❌ Supabase-Verbindungsfehler: {e}")
        send_telegram(f"⚠️ <b>Fehler:</b> Kann nicht mit Datenbank verbinden!")
        return
    
    checked = 0
    price_drops = 0
    errors = 0
    new_products = 0
    
    for product in PRODUCTS:
        name = product['name']
        url = product['url']
        
        print(f"\n📦 {name}")
        print(f"   🔗 {url[:60]}...")
        
        # Scrape aktuellen Preis
        current_price = scrape_amazon_price(url)
        
        if current_price is None:
            print(f"   ⚠️  Preis konnte nicht ermittelt werden")
            errors += 1
            send_telegram(f"⚠️ Konnte Preis nicht ermitteln für: <b>{name}</b>\n\nBitte prüfe die URL: {url}")
            continue
        
        print(f"   💰 Aktueller Preis: {current_price:.2f} €")
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
                    
                    print(f"   📉 PREISSENKUNG: {old_price:.2f} € → {current_price:.2f} € (-{discount_percent:.1f}%)")
                    price_drops += 1
                    
                    # Sende Telegram-Benachrichtigung
                    message = f"""🔔 <b>PREISALARM!</b> 🔔

📦 <b>{name}</b>

💰 Vorher: {old_price:.2f} €
✅ Jetzt: {current_price:.2f} €
📉 Ersparnis: {discount:.2f} € ({discount_percent:.1f}%)

🔗 <a href="{url}">Zum Produkt</a>"""
                    send_telegram(message)
                    
                    # Prüfe auf neuen Tiefstpreis
                    if current_price < lowest_price:
                        print(f"   🎉 NEUER TIEFSTPREIS!")
                        lowest_message = f"""🏆 <b>NEUER TIEFSTPREIS!</b> 🏆

📦 <b>{name}</b>
💎 Bester Preis ever: {current_price:.2f} €

🔗 <a href="{url}">Jetzt zuschlagen!</a>"""
                        send_telegram(lowest_message)
                
                elif current_price > old_price:
                    print(f"   📈 Preis gestiegen: {old_price:.2f} € → {current_price:.2f} €")
                else:
                    print(f"   ➡️  Preis unverändert")
                
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
                print(f"   ✨ Neues Produkt wird getrackt")
                new_product = {
                    'url': url,
                    'name': name,
                    'current_price': current_price,
                    'lowest_price': current_price
                }
                result = supabase.table('products').insert(new_product).execute()
                new_products += 1
                
                # Sende Info
                message = f"""✅ <b>Neues Produkt wird überwacht</b>

📦 {name}
💰 Startpreis: {current_price:.2f} €

Ich benachrichtige dich bei Preisänderungen!"""
                send_telegram(message)
                
        except Exception as e:
            print(f"   ❌ Datenbankfehler: {e}")
            errors += 1
        
        # Kleine Pause zwischen Produkten
        time.sleep(2)
    
    # Zusammenfassung
    print("\n" + "="*50)
    print(f"✅ Check abgeschlossen!")
    print(f"   📊 Produkte geprüft: {checked}")
    print(f"   ✨ Neue Produkte: {new_products}")
    print(f"   📉 Preissenkungen: {price_drops}")
    print(f"   ❌ Fehler: {errors}")
    
    # Sende Zusammenfassung nur bei Aktivität
    if price_drops > 0 or new_products > 0:
        summary = f"""📊 <b>Preis-Check abgeschlossen</b>

✅ {checked} Produkt{'e' if checked != 1 else ''} geprüft
✨ {new_products} neue{'s' if new_products == 1 else ''} Produkt{'e' if new_products != 1 else ''}
📉 {price_drops} Preissenkung{'en' if price_drops != 1 else ''}"""
        send_telegram(summary)

# ============================================
# HAUPTPROGRAMM
# ============================================

if __name__ == '__main__':
    try:
        check_prices()
    except Exception as e:
        print(f"❌ KRITISCHER FEHLER: {e}")
        import traceback
        traceback.print_exc()
        send_telegram(f"⚠️ <b>Kritischer Fehler beim Preis-Check:</b>\n\n{str(e)}")
        sys.exit(1)
