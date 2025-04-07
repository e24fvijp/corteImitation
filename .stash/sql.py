import sqlite3


class ConnectSQl:

    def __init__(self):
        self.conn = sqlite3.connect("data.db")
        self.cursor = self.conn.cursor()
        self._create_table()

    def insert_record(self, text, memo):
        self.cursor.execute("INSERT INTO records (text, memo) VALUES(?,?)",(text,memo))

    def _create_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            memo TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )                    
        """)

    def __del__(self):
        self.conn.commit()
        self.conn.close()
