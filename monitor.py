import sqlite3
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

FEEDS = [
    {"name": "Anthropic Blog", "url": "https://www.anthropic.com/rss.xml"},
    {"name": "Hacker News - Anthropic", "url": "https://hnrss.org/newest?q=anthropic&count=10"},
    {"name": "Hacker News - Claude AI", "url": "https://hnrss.org/newest?q=claude+ai&count=10"},
    {"name": "Reddit - ClaudeAI", "url": "https://www.reddit.com/r/ClaudeAI/.rss"}
]

def init_monitor_db():
    conn = sqlite3.connect("chats.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS monitored_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT, title TEXT, url TEXT, summary TEXT,
        collected_at TEXT, seen INTEGER DEFAULT 0, UNIQUE(url))""")
    conn.commit()
    conn.close()

def fetch_feed(feed):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(feed["url"], headers=headers, timeout=10)
        root = ET.fromstring(res.content)
        items = []
        for item in root.iter("item"):
            title = item.find("title")
            link = item.find("link")
            desc = item.find("description")
            if title is not None and link is not None:
                items.append({
                    "source": feed["name"],
                    "title": title.text or "",
                    "url": link.text or "",
                    "summary": desc.text[:300] if desc is not None and desc.text else ""
                })
        return items
    except Exception as e:
        print(f"Error fetching {feed['name']}: {e}")
        return []

def save_items(items):
    conn = sqlite3.connect("chats.db")
    new_count = 0
    for item in items:
        try:
            conn.execute("""INSERT OR IGNORE INTO monitored_items 
                (source, title, url, summary, collected_at, seen)
                VALUES (?, ?, ?, ?, ?, 0)""",
                (item["source"], item["title"], item["url"],
                 item["summary"], datetime.now().isoformat()))
            if conn.total_changes > 0:
                new_count += 1
        except:
            pass
    conn.commit()
    conn.close()
    return new_count

def run_monitor():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking feeds...")
    init_monitor_db()
    total_new = 0
    for feed in FEEDS:
        items = fetch_feed(feed)
        new = save_items(items)
        print(f"  {feed['name']}: {len(items)} fetched, {new} new")
        total_new += new
    print(f"  Total new items: {total_new}")
    return total_new

if __name__ == "__main__":
    run_monitor()
