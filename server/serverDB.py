import sqlite3
from enum import Enum

class Status(Enum):
    SUCCESS = 0
    INVALID_NAME = 1
    INVALID_PASSWORD = 2

DB_PATH = 'server.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        score INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

# Llamar a la inicialización al importar
init_db()

def name_exists(name : str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT 1 FROM players WHERE name = ?', (name,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def login(name : str, password : str) -> Status:
    if not name_exists(name):
        return Status.INVALID_NAME
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT 1 FROM players WHERE name = ? AND password = ?', (name, password))
    exists = c.fetchone() is not None
    if exists:
        return Status.SUCCESS
    else:
        return Status.INVALID_PASSWORD 

def signup(name : str, password : str) -> Status:
    if name_exists(name):
        return Status.INVALID_NAME
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO players (name, password) VALUES (?, ?)', (name, password))
    conn.commit()
    conn.close()
    return Status.SUCCESS
