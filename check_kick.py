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

KICK_API = "https://web.kick.com/api/v1/drops/campaigns"
SEEN_FILE = "seen_campaigns.json"


def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(list(seen)), f, indent=2)


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
        print("Telegram status:", r.status_code)
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
        print("HTTP status:", r.status_code)
    except Exception as e:
        print("Request error:", e)
        send_telegram(f"⚠️ <b>Kick check failed</b>\n\nNetwork error: {e}")
        return

    if r.status_code != 200:
        print("Bad status, aborting.")
        print(r.text[:300])
        send_telegram(
            f"⚠️ <b>Kick check failed</b>\n\n"
            f"HTTP status: {r.status_code}\n"
            f"Response: {r.text[:150]}"
        )
        return

    try:
        data = r.json()
    except Exception as e:
        print("JSON error:", e)
        send_telegram(f"⚠️ <b>Kick check failed</b>\n\nJSON parse error: {e}")
        return

    if isinstance(data, dict):
        campaigns = data.get("data", [])
    else:
        campaigns = data

    # শুধু active campaign
    campaigns = [c for c in campaigns if c.get("status") == "active"]
    print(f"Total active campaigns: {len(campaigns)}")

    seen = load_seen()
    new_found = []

    for c in campaigns:
        cid = str(c.get("id") or c.get("name"))
        if cid and cid not in seen:
            new_found.append((cid, c))

    print(f"New campaigns to notify: {len(new_found)}")

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    if new_found:
        for cid, c in new_found:
            title = c.get("name", "No title")
            org = (c.get("organization") or {}).get("name", "")
            starts = (c.get("starts_at") or "")[:16].replace("T", " ")
            ends = (c.get("ends_at") or "")[:16].replace("T", " ")
            rewards = c.get("rewards", [])
            reward_names = "\n".join([f"  • {r.get('name','')}" for r in rewards[:5]])
            if len(rewards) > 5:
                reward_names += f"\n  ... +{len(rewards)-5} more"

            msg = (
                f"🎯 <b>New Kick Campaign!</b>\n\n"
                f"<b>{title}</b>\n"
                f"🆔 <code>{cid}</code>\n"
                f"🏢 {org}\n"
                f"▶️ Start: {starts} UTC\n"
                f"⏹ End: {ends} UTC\n\n"
                f"🎁 Rewards:\n{reward_names}\n\n"
                f"🔗 https://kick.com/drops/campaigns"
            )
            send_telegram(msg)
            seen.add(cid)
            print("Sent:", title)

        save_seen(seen)
    else:
        print("No new active campaigns.")
        send_telegram(
            f"🔍 <b>Checked Kick campaigns</b>\n"
            f"✅ No new campaign found\n\n"
            f"🕒 {now}"
        )


if __name__ == "__main__":
    check_campaigns()
