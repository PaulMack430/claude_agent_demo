import sqlite3
import base64

DB_PATH = "chats.db"

def init_profile_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS profile (
        id INTEGER PRIMARY KEY,
        resume_filename TEXT,
        resume_base64 TEXT,
        cover_letter TEXT,
        github_repos TEXT,
        background_summary TEXT,
        updated_at TEXT
    )""")
    conn.commit()
    conn.close()

def save_profile(resume_filename=None, resume_base64=None, 
                  cover_letter=None, github_repos=None):
    conn = sqlite3.connect(DB_PATH)
    from datetime import datetime
    existing = conn.execute("SELECT id FROM profile LIMIT 1").fetchone()
    if existing:
        updates = []
        params = []
        if resume_filename:
            updates.append("resume_filename = ?")
            params.append(resume_filename)
        if resume_base64:
            updates.append("resume_base64 = ?")
            params.append(resume_base64)
        if cover_letter is not None:
            updates.append("cover_letter = ?")
            params.append(cover_letter)
        if github_repos is not None:
            updates.append("github_repos = ?")
            params.append(github_repos)
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(existing[0])
        conn.execute(f"UPDATE profile SET {', '.join(updates)} WHERE id = ?", params)
    else:
        conn.execute("""INSERT INTO profile 
            (resume_filename, resume_base64, cover_letter, github_repos, updated_at)
            VALUES (?, ?, ?, ?, ?)""",
            (resume_filename, resume_base64, cover_letter, 
             github_repos, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_profile():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM profile LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else {}

def profile_to_context(client) -> str:
    """Convert profile into context string for agents"""
    profile = get_profile()
    if not profile:
        return ""
    
    context = "\n=== CANDIDATE PROFILE ===\n"
    
    # Add GitHub repos
    if profile.get("github_repos"):
        context += f"\nGitHub Repos: {profile['github_repos']}\n"
    
    # Add cover letter
    if profile.get("cover_letter"):
        context += f"\nCover Letter:\n{profile['cover_letter']}\n"
    
    # Resume filename noted - full PDF reading disabled for performance
    if profile.get("resume_filename"):
        context += f"\nResume uploaded: {profile['resume_filename']}\n"
    
    context += "=== END CANDIDATE PROFILE ===\n"
    return context
