from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parents[1] / "niva_safe_incidents.db"

def connect():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.execute("PRAGMA journal_mode=WAL")
    return con

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            category TEXT NOT NULL,
            source TEXT NOT NULL,
            details TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            reviewer_note TEXT NOT NULL DEFAULT ''
        )""")

def create_incident(category, source, details, status="PENDING"):
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    with connect() as con:
        cur = con.execute("INSERT INTO incidents(timestamp, category, source, details, status) VALUES (?, ?, ?, ?, ?)",
                           (stamp, category, source, details, status))
        return int(cur.lastrowid)

def list_incidents(limit=50):
    with connect() as con:
        return con.execute("SELECT id, timestamp, category, source, details, status, reviewer_note FROM incidents ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()

def review_incident(incident_id, status, note=""):
    with connect() as con:
        con.execute("UPDATE incidents SET status = ?, reviewer_note = ? WHERE id = ?", (status, note.strip(), int(incident_id)))

def count_incidents(status=None):
    with connect() as con:
        if status:
            row = con.execute("SELECT COUNT(*) FROM incidents WHERE status = ?", (status,)).fetchone()
        else:
            row = con.execute("SELECT COUNT(*) FROM incidents").fetchone()
        return int(row[0])
