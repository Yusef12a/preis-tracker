#!/usr/bin/env python3
"""
🤖 SERVERLESS PREIS-TRACKER - MULTI-SHOP VERSION
Überwacht Preise auf Amazon & OTTO und benachrichtigt via Telegram.
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
# KONFIGURATION (GitHub Secrets)
# ============================================

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Deine Produktliste (Nutze lange URLs für OTTO!)
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
        'url': 'https://www.otto.de/p/sony-wf-c700n-wireless-in-ear-kopfhoerer-noise-cancelling-bluetooth-bis-20-std-akkulaufzeit-multipoint-connection-1729365155/'
    }
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
]

# ============================================
# FUNKTIONEN
# ============================================

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
        response = requests.post(url, data=data, timeout=10)
        return response.ok
    except Exception as e:
        print(f"❌ Telegram-Fehler: {e}")
        return False

def extract_price(text):
    try:
        text = text.replace(' ', '').replace('\xa0', '').replace('*', '')
        # Sucht nach Formaten wie 199,00 oder 199.00
        match = re.search(r'(\d+)[,.](\d{2})', text)
        if match:
            return float(f"{match.group(1)}.{match.group(2)}")
        # Spezialfall OTTO: Nur Ganze Zahlen vor dem Eurozeichen
        match_simple = re.search(r'(\d+)', text)
        if match_simple:
            return float(match_simple.group(1))
        return None
    except:
        return None

def scrape_price(url):
    """Scrapt Preise von Amazon oder OTTO"""
    for user_agent in USER_AGENTS:
        headers = {
            'User-Agent': user_agent,
            'Accept-Language': 'de-DE,de;q=0.9',
            'Referer': 'https://www.google.com/'
        }
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Liste aller möglichen Preis-Elemente (Amazon & OTTO)
            price_selectors = [
                '.a-price .a-offscreen', 'span.a-price-whole', # Amazon
                '.p_price__inner', '.pd_price__main', 'span[itemprop="price"]', # OTTO
                '.js_purchasePrice', '.price__amount', '[data-qa="product-price"]' # Allgemein
            ]
            
            for selector in price_selectors:
                element = soup.select_one(selector)
                if element:
                    price = extract_price(element.get_text())
                    if price and 1.0 < price < 10000.0:
                        return price
            
            # Fallback: Suche im gesamten Text nach Euro-Mustern
            text_snippet = soup.get_text()
            match = re.search(r'(\d+[,.]\d{2})\s*€', text_snippet)
            if match:
                return extract_price(match.group(1))

        except Exception as e:
            print(f"⚠️ Fehler beim Scraping: {e}")
            continue
    return None

def check_prices():
    print(f"🚀 Starte Preis-Check am {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    
    if not all([SUPABASE_URL, SUPABASE_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        print("❌ KRITISCHER FEHLER: Secrets fehlen!")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    for product in PRODUCTS:
        name = product['name']
        url = product['url']
        print(f"\n🔍 Prüfe: {name}")
        
        current_price = scrape_price(url)
        
        if current_price is None:
            print(f"  ⚠️ Preis nicht gefunden.")
            send_telegram(f"⚠️ Konnte Preis nicht ermitteln für: <b>{name}</b>\nURL prüfen!")
            continue

        print(f"  💰 Preis: {current_price:.2f} €")
        
        # DB Abgleich
        res = supabase.table('products').select('*').eq('url', url).execute()
        
        if res.data:
            p_id = res.data[0]['id']
            old_price = float(res.data[0]['current_price'] or 0)
            lowest = float(res.data[0]['lowest_price'] or current_price)
            
            if current_price < old_price and old_price > 0:
                diff = old_price - current_price
                send_telegram(f"🔔 <b>PREISALARM!</b>\n\n📦 {name}\n💰 Alt: {old_price:.2f}€\n✅ Neu: <b>{current_price:.2f}€</b>\n📉 Ersparnis: {diff:.2f}€\n\n<a href='{url}'>Zum Shop</a>")
            
            # Update DB
            supabase.table('products').update({
                'current_price': current_price,
                'lowest_price': min(current_price, lowest),
                'last_checked': datetime.now().isoformat()
            }).eq('id', p_id).execute()
            
            # Historie
            supabase.table('price_history').insert({'product_id': p_id, 'price': current_price}).execute()
        else:
            # Neu anlegen
            supabase.table('products').insert({
                'name': name, 'url': url, 'current_price': current_price, 'lowest_price': current_price
            }).execute()
            send_telegram(f"✅ Neues Produkt im Tracking:\n<b>{name}</b>\nStartpreis: {current_price:.2f}€")

        time.sleep(2)

if __name__ == '__main__':
    check_prices()
