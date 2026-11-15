"""SQLite persistence for reviewer decisions and the savings ledger.

Rows are keyed by (session, pack) so two judges using the same hosted demo never see each other's decisions,
and switching industry keeps each industry's decisions separate.
"""
import os
import sqlite3
import tempfile

DB_PATH = os.environ.get("PARTLINK_DB", os.path.join(tempfile.gettempdir(), "partlink.db"))


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("CREATE TABLE IF NOT EXISTS decisions(session TEXT, pack TEXT, spend_id TEXT, part TEXT, "
              "PRIMARY KEY(session, pack, spend_id))")
    c.execute("CREATE TABLE IF NOT EXISTS ledger(session TEXT, pack TEXT, opp TEXT, status TEXT, "
              "PRIMARY KEY(session, pack, opp))")
    return c


def load_decisions(session, pack) -> dict:
    with _conn() as c:
        return dict(c.execute("SELECT spend_id, part FROM decisions WHERE session=? AND pack=?", (session, pack)))


def save_decisions(session, pack, decisions: dict):
    with _conn() as c:
        c.execute("DELETE FROM decisions WHERE session=? AND pack=?", (session, pack))
        c.executemany("INSERT INTO decisions VALUES (?,?,?,?)", [(session, pack, k, v) for k, v in decisions.items()])


def load_ledger(session, pack) -> dict:
    with _conn() as c:
        return dict(c.execute("SELECT opp, status FROM ledger WHERE session=? AND pack=?", (session, pack)))


def save_ledger(session, pack, status: dict):
    with _conn() as c:
        c.execute("DELETE FROM ledger WHERE session=? AND pack=?", (session, pack))
        c.executemany("INSERT INTO ledger VALUES (?,?,?,?)", [(session, pack, k, v) for k, v in status.items()])
