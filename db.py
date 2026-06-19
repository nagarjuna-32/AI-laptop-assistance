import sqlite3
import os
import json
from datetime import datetime

DB_FILE = "jarvis.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL
        )
    """)
    
    # 2. custom_commands table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_phrase TEXT UNIQUE NOT NULL,
            aliases_json TEXT NOT NULL,
            actions_json TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # 3. memory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # 4. projects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT UNIQUE NOT NULL,
            details_json TEXT NOT NULL,
            deadline TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # 5. app_paths table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_paths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT UNIQUE NOT NULL,
            executable_path TEXT,
            web_fallback TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # 6. notes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # 7. tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            status TEXT NOT NULL,
            deadline TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # 8. voice_devices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voice_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT UNIQUE NOT NULL,
            device_type TEXT NOT NULL,
            priority INTEGER NOT NULL,
            selected INTEGER DEFAULT 0,
            last_used TEXT NOT NULL
        )
    """)
    
    # 9. action_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            heard_text TEXT,
            intent TEXT,
            action TEXT,
            status TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    
    # Seed default settings
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        seed_settings(cursor)
        
    # Seed default custom commands
    cursor.execute("SELECT COUNT(*) FROM custom_commands")
    if cursor.fetchone()[0] == 0:
        seed_custom_commands(cursor)
        
    # Seed default app paths
    cursor.execute("SELECT COUNT(*) FROM app_paths")
    if cursor.fetchone()[0] == 0:
        seed_app_paths(cursor)
        
    conn.commit()
    conn.close()

def seed_settings(cursor):
    defaults = [
        ("os_access_allowed", "0"),
        ("background_listening", "1"),
        ("wake_command_enabled", "0"),
        ("auto_execute_safe", "1"),
        ("voice_rate", "170"),
        ("voice_volume", "1.0")
    ]
    for k, v in defaults:
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

def seed_custom_commands(cursor):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    defaults = [
        (
            "study mode", 
            ["start study mode", "activate study mode", "open study mode", "turn on study mode"],
            ["open ChatGPT", "open YouTube", "open WhatsApp"]
        ),
        (
            "coding mood", 
            ["coding mode", "start coding mood", "activate coding mood", "open coding mode"],
            ["open Gemini", "open ChatGPT", "open Antigravity IDE", "open Spotify"]
        ),
        (
            "placement mode",
            ["start placement mode", "activate placement mode", "open placement mode"],
            ["open Resume", "open LinkedIn", "open ChatGPT", "open Interview Dashboard"]
        ),
        (
            "project mode",
            ["start project mode", "activate project mode", "open project mode"],
            ["open AIPlacement", "open Portfolio", "open Full Stack Projects", "open Internship Tasks"]
        )
    ]
    for phrase, aliases, actions in defaults:
        cursor.execute("""
            INSERT OR IGNORE INTO custom_commands 
            (trigger_phrase, aliases_json, actions_json, enabled, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?)
        """, (phrase, json.dumps(aliases), json.dumps(actions), timestamp, timestamp))

def seed_app_paths(cursor):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    defaults = [
        ("ChatGPT", "", "https://chatgpt.com"),
        ("Gemini", "", "https://gemini.google.com"),
        ("YouTube", "", "https://youtube.com"),
        ("WhatsApp", "", "https://web.whatsapp.com"),
        ("Spotify", "", "https://open.spotify.com"),
        ("Antigravity IDE", "", ""),
        ("Resume", "", "https://www.linkedin.com"),
        ("LinkedIn", "", "https://www.linkedin.com"),
        ("Interview Dashboard", "", "https://leetcode.com"),
        ("AIPlacement", "", "https://github.com"),
        ("Portfolio", "", "https://github.com"),
        ("Full Stack Projects", "", "https://github.com"),
        ("Internship Tasks", "", "https://github.com")
    ]
    for name, path, fallback in defaults:
        cursor.execute("""
            INSERT OR IGNORE INTO app_paths 
            (app_name, executable_path, web_fallback, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, path, fallback, timestamp, timestamp))

# Settings helper functions
def get_setting(key, default=""):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

# Custom commands helpers
def add_custom_command(phrase, actions_list, aliases_list=None, enabled=1):
    init_db()
    phrase_clean = phrase.lower().strip()
    aliases = aliases_list or []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO custom_commands 
            (trigger_phrase, aliases_json, actions_json, enabled, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (phrase_clean, json.dumps(aliases), json.dumps(actions_list), enabled, timestamp, timestamp))
        conn.commit()
        success = True
    except Exception as e:
        print(f"Error adding custom command: {e}")
        success = False
    finally:
        conn.close()
    return success

def update_custom_command(cmd_id, phrase, actions_list, aliases_list=None, enabled=1):
    init_db()
    phrase_clean = phrase.lower().strip()
    aliases = aliases_list or []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE custom_commands 
            SET trigger_phrase = ?, aliases_json = ?, actions_json = ?, enabled = ?, updated_at = ?
            WHERE id = ?
        """, (phrase_clean, json.dumps(aliases), json.dumps(actions_list), enabled, timestamp, cmd_id))
        conn.commit()
        success = cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating custom command: {e}")
        success = False
    finally:
        conn.close()
    return success

def toggle_custom_command(cmd_id, enabled):
    init_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE custom_commands 
            SET enabled = ?, updated_at = ?
            WHERE id = ?
        """, (enabled, timestamp, cmd_id))
        conn.commit()
        success = cursor.rowcount > 0
    except Exception as e:
        print(f"Error toggling custom command: {e}")
        success = False
    finally:
        conn.close()
    return success

def get_custom_command_by_phrase(phrase):
    init_db()
    phrase_clean = phrase.lower().strip()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT actions_json FROM custom_commands 
        WHERE trigger_phrase = ? AND enabled = 1
    """, (phrase_clean,))
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row[0])
        except Exception:
            return []
    return None

def get_all_custom_commands():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, trigger_phrase, aliases_json, actions_json, enabled 
        FROM custom_commands ORDER BY trigger_phrase ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        try:
            aliases = json.loads(r[2])
        except Exception:
            aliases = []
        try:
            acts = json.loads(r[3])
        except Exception:
            acts = []
        res.append({
            "id": r[0],
            "trigger_phrase": r[1],
            "aliases": aliases,
            "actions": acts,
            "enabled": bool(r[4])
        })
    return res

def get_all_enabled_custom_commands():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT trigger_phrase, aliases_json, actions_json 
        FROM custom_commands WHERE enabled = 1
    """)
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        try:
            aliases = json.loads(r[1])
        except Exception:
            aliases = []
        try:
            acts = json.loads(r[2])
        except Exception:
            acts = []
        res.append({
            "trigger_phrase": r[0],
            "aliases": aliases,
            "actions": acts
        })
    return res

def get_active_custom_commands_count():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM custom_commands WHERE enabled = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def delete_custom_command_by_id(cmd_id):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM custom_commands WHERE id = ?", (cmd_id,))
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count > 0

# App paths helpers
def get_app_path(app_name):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT executable_path, web_fallback FROM app_paths 
        WHERE app_name = ?
    """, (app_name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"executable_path": row[0], "web_fallback": row[1]}
    return None

def set_app_path(app_name, exe_path, fallback=""):
    init_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM app_paths WHERE app_name = ?", (app_name,))
    row = cursor.fetchone()
    if row:
        cursor.execute("""
            UPDATE app_paths 
            SET executable_path = ?, web_fallback = ?, updated_at = ?
            WHERE app_name = ?
        """, (exe_path, fallback, timestamp, app_name))
    else:
        cursor.execute("""
            INSERT INTO app_paths 
            (app_name, executable_path, web_fallback, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (app_name, exe_path, fallback, timestamp, timestamp))
    conn.commit()
    conn.close()

# Device helpers
def get_voice_devices():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, device_name, device_type, priority, selected FROM voice_devices ORDER BY priority ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{
        "id": r[0],
        "device_name": r[1],
        "device_type": r[2],
        "priority": r[3],
        "selected": bool(r[4])
    } for r in rows]

def set_selected_device(device_name):
    init_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE voice_devices SET selected = 0")
    cursor.execute("UPDATE voice_devices SET selected = 1, last_used = ? WHERE device_name = ?", (timestamp, device_name))
    conn.commit()
    conn.close()

def add_voice_device(device_name, device_type, priority, selected=0):
    init_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO voice_devices 
            (device_name, device_type, priority, selected, last_used)
            VALUES (?, ?, ?, ?, ?)
        """, (device_name, device_type, priority, selected, timestamp))
        conn.commit()
    except Exception as e:
        print(f"Error adding voice device: {e}")
    finally:
        conn.close()

def clear_voice_devices():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM voice_devices")
    conn.commit()
    conn.close()

# Action logs helpers
def add_action_log(heard_text, intent_name, action_preview, status):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("""
            INSERT INTO action_logs (heard_text, intent, action, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (heard_text, intent_name, action_preview, status, timestamp))
        conn.commit()
    except Exception as e:
        print(f"Error logging action: {e}")
    finally:
        conn.close()

def get_action_logs(limit=30):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT created_at, heard_text, intent, action, status 
        FROM action_logs ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{
        "timestamp": r[0],
        "phrase": r[1],
        "intent": r[2],
        "action": r[3],
        "status": r[4]
    } for r in rows]

# ----------------- NEW PORTFOLIO / METADATA HELPERS -----------------
# 1. Notes Helpers
def add_note(title, content):
    init_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)", (title, content, timestamp, timestamp))
    conn.commit()
    conn.close()

def get_all_notes():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, created_at FROM notes ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "content": r[2], "created_at": r[3]} for r in rows]

def delete_note(note_id):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

# 2. Tasks Helpers
def add_task(name, status="Pending", deadline=""):
    init_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (task_name, status, deadline, created_at, updated_at) VALUES (?, ?, ?, ?, ?)", (name, status, deadline, timestamp, timestamp))
    conn.commit()
    conn.close()

def get_all_tasks():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_name, status, deadline FROM tasks ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "task_name": r[1], "status": r[2], "deadline": r[3]} for r in rows]

def update_task_status(task_id, status):
    init_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?", (status, timestamp, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# 3. Memory Helpers
def add_memory(key, value):
    init_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO memory (key, value, created_at) VALUES (?, ?, ?)", (key, value, timestamp))
    conn.commit()
    conn.close()

def get_memory(key, default=""):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM memory WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def get_all_memory():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM memory ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

# 4. Projects Helpers
def add_project(name, details, deadline="", status="In Progress"):
    init_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO projects 
            (project_name, details_json, deadline, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, json.dumps(details), deadline, status, timestamp, timestamp))
        conn.commit()
    except Exception as e:
        print(f"Error adding project: {e}")
    finally:
        conn.close()

def get_all_projects():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, project_name, details_json, deadline, status FROM projects ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        try:
            details = json.loads(r[2])
        except Exception:
            details = {}
        res.append({
            "id": r[0],
            "project_name": r[1],
            "details": details,
            "deadline": r[3],
            "status": r[4]
        })
    return res

def delete_project(project_id):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

# Migration check
def check_migration():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # If memory table doesn't exist, we recreate DB
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory'")
        row = cursor.fetchone()
        if not row:
            print("Recreating database for updated Chinni tables...")
            cursor.execute("DROP TABLE IF EXISTS custom_commands")
            cursor.execute("DROP TABLE IF EXISTS app_paths")
            cursor.execute("DROP TABLE IF EXISTS settings")
            cursor.execute("DROP TABLE IF EXISTS voice_devices")
            cursor.execute("DROP TABLE IF EXISTS action_logs")
            conn.commit()
    except Exception:
        pass
    finally:
        conn.close()

check_migration()
init_db()

# Force wake_command_enabled to 0 on launch to disable wake word detection by default
def force_disable_wake_word():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = '0' WHERE key = 'wake_command_enabled'")
    conn.commit()
    conn.close()

try:
    force_disable_wake_word()
except Exception:
    pass

