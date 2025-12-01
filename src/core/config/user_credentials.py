import sqlite3
from pathlib import Path
from os import makedirs
from platformdirs import user_config_dir
from dataclasses import dataclass, asdict
import json

data_path = user_config_dir('RyujinApp')
db_path = Path(data_path) / 'credentials.db'
makedirs(data_path, exist_ok=True)

@dataclass
class UserCredentials:
    provider: str
    email: str
    password: str

    def as_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

def init_credentials_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS credentials (
                        provider TEXT PRIMARY KEY,
                        email TEXT,
                        password TEXT
                      )''')
    conn.commit()
    conn.close()

def save_credentials(provider: str, email: str, password: str) -> None:
    init_credentials_db()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO credentials (provider, email, password) VALUES (?, ?, ?)',
                   (provider, email, password))
    conn.commit()
    conn.close()

def get_credentials(provider: str) -> UserCredentials | None:
    init_credentials_db()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM credentials WHERE provider = ?', (provider,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return UserCredentials(provider=row[0], email=row[1], password=row[2])

def delete_credentials(provider: str) -> None:
    init_credentials_db()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM credentials WHERE provider = ?', (provider,))
    conn.commit()
    conn.close()

def has_credentials(provider: str) -> bool:
    return get_credentials(provider) is not None
