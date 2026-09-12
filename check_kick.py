import requests
import json
import os
from datetime import datetime

# ===== আপনার তথ্য =====
KICK_SESSION_TOKEN = "428436484%7CJg4kvSfD4mqNZHKoD34Eryk3kjfsYDtRck6jtgxh"
KICK_SESSION = "eyJpdiI6InpNM2REM1BacmxmZ2FCVE1SWGdmN1E9PSIsInZhbHVlIjoiUUJtNitxT3BYQk56Q1Q1QTdHbUNsMFhNYW1yYXZUWHZmZjRpMmNralRlV0EzK1hGUHZha0xENGxxMS80NUIwNWROWEZCZEgxU2VLR202eW1LTnhFWm5wMXh3YWg1K3hlUXgwOFdMY2JGNGQzUTNHdFpFNHZ5Y0s0MS9hZk9JVC8iLCJtYWMiOiI3MzVjZWEzOTc2ODNhOTY4ZTViNjcyYzc4NGE5OWYwNzMyMmVkOWY5ZTJlMzdiMzc5Nzk1Zjg1YjJlNGQ0M2ExIiwidGFnIjoiIn0%3D"
TELEGRAM_BOT_TOKEN = "8969698368:AAG52crkSkwsVEV6_m4i547AGWv6eoxUhLw"
TELEGRAM_CHAT_ID = "8949091966"
# ======================

KICK_API = "https://kick.com/api/v2/campaigns"
SEEN_FILE = "seen_campaigns.json"


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        print("Telegram response:", r.status_code)
    except Exception as e:
        print("Telegram error:", e)


def check_campaigns():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://kick.com/drops/campaigns",
        "Origin": "https://kick.com",
        "Cookie": f"session_token={KICK_SESSION_TOKEN}; kick_session={KICK_SESSION}",
    }

    try:
        r = requests.get(KICK_API, headers=headers, timeout=20)
        print("Status:", r.status_code)
        print("Response preview:", r.text[:500])
    except Exception as e:
        print("Request error:", e)
        return

    if r.status_code != 200:
        print("Failed. Not 200.")
        return

    try:
        data = r.json()
    except Exception as e:
        print("JSON parse error:", e)
        return

    # response structure handle
    if isinstance(data, list):
        campaigns = data
    elif isinstance(data, dict):
        campaigns = data.get("data") or data.get("campaigns") or []
    else:
        campaigns = []

    if not campaigns:
        print("No campaigns in response.")
        return

    seen = load_seen()
    new_found = []

    for c in campaigns:
        cid = str(c.get("id") or c.get("slug") or c.get("title") or c.get("name"))
        if cid not in seen:
            seen.add(cid)
            new_found.append(c)

    if new_found:
        for c in new_found:
            title = c.get("title") or c.get("name") or "Unknown"
            desc = (c.get("description") or "")[:200]
            msg = (
                f"🎯 <b>New Kick Campaign!</b>\n\n"
                f"<b>{title}</b>\n"
                f"{desc}\n\n"
                f"🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"🔗 https://kick.com/drops/campaigns"
            )
            send_telegram(msg)
            print("Sent:", title)
        save_seen(seen)
    else:
        print("No new campaigns.")


if __name__ == "__main__":
    check_campaigns()
