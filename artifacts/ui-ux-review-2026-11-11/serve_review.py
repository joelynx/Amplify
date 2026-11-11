"""Temporary UI review bridge. Uses an isolated snapshot of the user's database."""
import json
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from app.ipc.api import Api

DB = Path(__file__).with_name('review.db')
if not DB.exists() or DB.stat().st_size < 4096:
    with sqlite3.connect((ROOT / 'app/data/appdata/amplify.db').as_uri() + '?mode=ro', uri=True) as source:
        with sqlite3.connect(DB) as target:
            schema = source.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            for name, sql in schema:
                target.execute(sql)
                cols = [r[1] for r in source.execute(f'PRAGMA table_info("{name}")')]
                expr = ','.join('NULL' if c in ('similarity_emb', 'classification_emb') else f'"{c}"' for c in cols)
                rows = source.execute(f'SELECT {expr} FROM "{name}"')
                while chunk := rows.fetchmany(200):
                    target.executemany(f'INSERT INTO "{name}" VALUES ({",".join("?" for _ in cols)})', chunk)
            target.commit()

def connect():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys = ON')
    return c

api = Api(connect)
ALLOWED_PREFIX = ('get_', 'list_', 'count_', 'load_', 'search_', 'quiz_', 'resolve_', 'check_')
ALLOWED = {'ping', 'log', 'set_config', 'set_theme', 'activate_subject', 'validate_header_text'}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def respond(self, status=200):
        self.send_response(status)
        self.send_header('Access-Control-Allow-Origin', 'http://127.0.0.1:5179')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

    def do_OPTIONS(self):
        self.respond()

    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            method = body['method']
            if method not in ALLOWED and not method.startswith(ALLOWED_PREFIX):
                raise ValueError('Blocked during review: ' + method)
            value = getattr(api, method)(*body.get('args', []))
            self.respond()
            self.wfile.write(json.dumps({'value': value}).encode())
        except Exception as e:
            print(type(e).__name__, str(e), flush=True)
            self.respond(500)
            self.wfile.write(json.dumps({'error': str(e)}).encode())
        finally:
            conn = getattr(api._local, 'conn', None)
            if conn:
                conn.close()
                del api._local.conn

print('Review bridge ready on 8766; isolated database', flush=True)
ThreadingHTTPServer(('127.0.0.1', 8766), Handler).serve_forever()
