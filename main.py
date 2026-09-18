import os
import json
import sqlite3
import webbrowser
import threading
from datetime import datetime
from anthropic import Anthropic
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()
client = Anthropic()

def init_db():
    conn = sqlite3.connect("chats.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, created_at TEXT, updated_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER, role TEXT, content TEXT, created_at TEXT)""")
    conn.commit()
    conn.close()

init_db()

SYSTEM_PROMPT = """You are a job intelligence agent helping someone apply for the Anthropic Technical Evangelist role. Search the web for every question. Be specific with names, dates, and links. Always cite sources."""

class MessageRequest(BaseModel):
    conversation_id: Optional[int] = None
    message: str


def search_chat_history(query: str, limit: int = 5) -> str:
    """Search past conversations for relevant context"""
    conn = get_db()
    keywords = [w.lower() for w in query.split() if len(w) > 3]
    if not keywords:
        return ""
    
    conditions = " OR ".join([f"LOWER(content) LIKE ?" for _ in keywords])
    params = [f"%{kw}%" for kw in keywords]
    
    rows = conn.execute(f"""
        SELECT role, content, created_at 
        FROM messages 
        WHERE ({conditions})
        AND role IN ('user', 'assistant')
        ORDER BY created_at DESC
        LIMIT ?
    """, params + [limit]).fetchall()
    conn.close()
    
    if not rows:
        return ""
    
    context = "\n\n=== RELEVANT PAST CONVERSATIONS ===\n"
    for row in rows:
        role = "You" if row["role"] == "user" else "Agent"
        context += f"{role}: {row['content'][:500]}\n---\n"
    context += "=== END OF PAST CONVERSATIONS ===\n\n"
    return context

def get_db():
    conn = sqlite3.connect("chats.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
def root():
    with open("index.html") as f:
        return f.read()

@app.get("/conversations")
def get_conversations():
    conn = get_db()
    rows = conn.execute("SELECT * FROM conversations ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/conversations")
def create_conversation():
    conn = get_db()
    now = datetime.now().isoformat()
    cursor = conn.execute("INSERT INTO conversations (title, created_at, updated_at) VALUES (?, ?, ?)", ("New Chat", now, now))
    conn.commit()
    conv_id = cursor.lastrowid
    conn.close()
    return {"id": conv_id, "title": "New Chat", "created_at": now}

@app.get("/conversations/{conv_id}/messages")
def get_messages(conv_id: int):
    conn = get_db()
    rows = conn.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at", (conv_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: int):
    conn = get_db()
    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
    conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}

@app.post("/chat")
def chat(req: MessageRequest):
    conn = get_db()
    now = datetime.now().isoformat()
    if not req.conversation_id:
        cursor = conn.execute("INSERT INTO conversations (title, created_at, updated_at) VALUES (?, ?, ?)", (req.message[:50], now, now))
        conn.commit()
        conv_id = cursor.lastrowid
    else:
        conv_id = req.conversation_id
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id))
        conn.commit()
    conn.execute("INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)", (conv_id, "user", req.message, now))
    conn.commit()
    history = conn.execute("SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at", (conv_id,)).fetchall()
    claude_messages = [{"role": r["role"], "content": r["content"]} for r in history if r["role"] in ["user", "assistant"]]
    conn.close()

    def generate():
        full_response = ""
        yield f"data: {json.dumps({'conv_id': conv_id})}\n\n"
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=claude_messages
        )
        for block in response.content:
            if hasattr(block, "text"):
                full_response += block.text
                for word in block.text.split(" "):
                    yield f"data: {json.dumps({'text': word + ' '})}\n\n"
        save_conn = sqlite3.connect("chats.db")
        save_conn.execute("INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)", (conv_id, "assistant", full_response, datetime.now().isoformat()))
        save_conn.commit()
        save_conn.close()
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
@app.get("/briefing")
def get_briefing():
    from monitor import run_monitor, init_monitor_db
    init_monitor_db()
    run_monitor()
    conn = get_db()
    items = conn.execute("""
        SELECT source, title, url, summary, collected_at 
        FROM monitored_items 
        ORDER BY collected_at DESC 
        LIMIT 20
    """).fetchall()
    conn.close()
    if not items:
        return {"briefing": "No new items found.", "count": 0}
    content = "\n\n".join([
        f"Source: {i['source']}\nTitle: {i['title']}\nURL: {i['url']}\nSummary: {i['summary']}"
        for i in items
    ])
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"Summarize these recent Anthropic/Claude news items into a brief morning briefing. Highlight anything relevant to someone applying for the Anthropic Technical Evangelist role:\n\n{content}"
        }]
    )
    return {
        "briefing": response.content[0].text,
        "count": len(items)
    }

@app.get("/briefing/count")
def get_unseen_count():
    from monitor import init_monitor_db
    init_monitor_db()
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM monitored_items WHERE seen = 0").fetchone()[0]
    conn.close()
    return {"unseen": count}

@app.post("/interview-prep")
def interview_prep(req: dict):
    from agents import run_interview_prep_pipeline
    from profile import profile_to_context, init_profile_db
    import json as json2
    import threading
    init_profile_db()
    background = req.get("background", "")
    # Only use profile for interview prep - no RAG to avoid hallucination
    from profile import get_profile
    profile = get_profile()
    profile_parts = []
    if profile.get("cover_letter"):
        profile_parts.append(f"Cover Letter:\n{profile['cover_letter']}")
    if profile.get("github_repos"):
        profile_parts.append(f"GitHub Repos:\n{profile['github_repos']}")
    full_background = "\n\n".join(profile_parts) + "\n\n" + background if profile_parts else background
    progress_list = []
    result_box = {}
    error_box = {}

    def callback(msg):
        progress_list.append(msg)

    def run():
        try:
            result_box["r"] = run_interview_prep_pipeline(full_background, callback)
        except Exception as e:
            error_box["e"] = str(e)

    def generate():
        t = threading.Thread(target=run)
        t.start()
        sent = 0
        while t.is_alive() or sent < len(progress_list):
            while sent < len(progress_list):
                msg = progress_list[sent]
                yield "data: " + json2.dumps({"progress": msg}) + "\n\n"
                sent += 1
            t.join(timeout=0.5)
        if "e" in error_box:
            yield "data: " + json2.dumps({"error": error_box["e"]}) + "\n\n"
        elif "r" in result_box:
            yield "data: " + json2.dumps({"document": result_box["r"]["document"]}) + "\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/profile")
def get_profile_route():
    from profile import get_profile, init_profile_db
    init_profile_db()
    return get_profile()

@app.post("/profile/repos")
def save_repos(req: dict):
    from profile import save_profile, init_profile_db
    init_profile_db()
    save_profile(github_repos=req.get("repos", ""))
    return {"status": "saved"}

@app.post("/profile/cover-letter")
def save_cover_letter(req: dict):
    from profile import save_profile, init_profile_db
    init_profile_db()
    save_profile(cover_letter=req.get("cover_letter", ""))
    return {"status": "saved"}

@app.post("/profile/resume")
async def save_resume(request: Request):
    from profile import save_profile, init_profile_db
    import base64
    init_profile_db()
    form = await request.form()
    file = form.get("file")
    if file:
        contents = await file.read()
        b64 = base64.b64encode(contents).decode("utf-8")
        save_profile(resume_filename=file.filename, resume_base64=b64)
        return {"status": "saved", "filename": file.filename}
    return {"status": "error", "message": "No file provided"}

if __name__ == "__main__":
    import uvicorn
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:8000")).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
