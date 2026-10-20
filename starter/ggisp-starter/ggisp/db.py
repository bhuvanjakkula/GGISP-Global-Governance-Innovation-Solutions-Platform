"""SQLite schema and persistence. All records are local to this prototype."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DOMAINS = [
    ("nuclear-security", "Nuclear security", "Peaceful safeguards, risk reduction and verification research", "high"),
    ("un-security-council", "UN Security Council", "Institutional reform and diplomatic mechanisms", "policy"),
    ("wto-trade", "WTO and global trade", "Trade rules, market access and dispute analysis", "policy"),
    ("sovereign-debt", "Global sovereign debt", "Transparent debt sustainability and restructuring", "economic"),
    ("ai-governance", "AI governance", "Accountability, safety and interoperability", "technology"),
    ("cybersecurity", "Cybersecurity", "Defensive cybersecurity cooperation and incident governance", "high"),
    ("global-health", "Global health", "Equitable health systems and epidemiological intelligence", "high"),
    ("space-security", "Space security", "Space traffic safety, debris and peaceful space use", "high"),
    ("critical-minerals", "Critical minerals", "Supply chains, traceability and fair access", "economic"),
    ("ocean-governance", "Ocean governance", "Marine ecosystems, fisheries and ocean law", "environment"),
    ("international-tax", "International taxation", "Cross-border transparency and policy simulation", "economic"),
    ("development-finance", "Global development finance", "Development investments and funding outcomes", "economic"),
    ("climate-finance", "Climate and environmental finance", "Climate adaptation, emissions and funding allocation", "environment"),
]


def database_path() -> Path:
    return Path(os.getenv("GGISP_DB_PATH", str(ROOT / "data" / "ggisp.db")))


@contextmanager
def db():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db() -> None:
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS domains (
            slug TEXT PRIMARY KEY, name TEXT NOT NULL,
            description TEXT NOT NULL, family TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_slug TEXT NOT NULL REFERENCES domains(slug),
            title TEXT NOT NULL, problem TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'concept',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            title TEXT NOT NULL, url TEXT NOT NULL, publisher TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '', manually_reviewed INTEGER NOT NULL DEFAULT 0,
            accessed_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            statement TEXT NOT NULL, evidence_status TEXT NOT NULL DEFAULT 'unverified',
            source_id INTEGER REFERENCES sources(id), limitations TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            recommendation TEXT NOT NULL, rationale TEXT NOT NULL,
            risks TEXT NOT NULL, author TEXT NOT NULL DEFAULT 'Founder',
            approval_status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            approved_at TEXT
        );
        CREATE TABLE IF NOT EXISTS ai_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            output_text TEXT NOT NULL, model TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER,
            action TEXT NOT NULL, record_type TEXT NOT NULL,
            record_id INTEGER, happened_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """)
        for d in DOMAINS:
            con.execute("INSERT OR IGNORE INTO domains (slug,name,description,family) VALUES (?,?,?,?)", d)
        # A no-facts demo project: examples are illustrative, never current-country assertions.
        n = con.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        if n == 0:
            con.execute(
                "INSERT INTO projects (domain_slug,title,problem) VALUES (?,?,?)",
                ("sovereign-debt", "DEMO: Sovereign debt policy sandbox",
                 "How might alternative interest, growth and primary-balance assumptions change a stylized debt path? No country-specific findings have been entered."),
            )
