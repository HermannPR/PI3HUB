import os, sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if DATABASE_URL:
    import psycopg2

    def _conn():
        return psycopg2.connect(DATABASE_URL)

    def init():
        with _conn() as con:
            con.cursor().execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id SERIAL PRIMARY KEY,
                    nick TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            con.commit()

    def submit(nick: str, score: int):
        with _conn() as con:
            con.cursor().execute(
                "INSERT INTO scores (nick, score) VALUES (%s, %s)",
                (nick.upper()[:4], score)
            )
            con.commit()

    def leaderboard():
        with _conn() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT nick, MAX(score) FROM scores GROUP BY nick ORDER BY MAX(score) DESC LIMIT 10"
            )
            rows = cur.fetchall()
        return [{"rank": i + 1, "nick": r[0], "score": r[1]} for i, r in enumerate(rows)]

else:
    DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores.db")

    def init():
        with sqlite3.connect(DB) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nick TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)

    def submit(nick: str, score: int):
        with sqlite3.connect(DB) as con:
            con.execute("INSERT INTO scores (nick, score) VALUES (?, ?)",
                        (nick.upper()[:4], score))

    def leaderboard():
        with sqlite3.connect(DB) as con:
            rows = con.execute(
                "SELECT nick, MAX(score) FROM scores GROUP BY nick ORDER BY MAX(score) DESC LIMIT 10"
            ).fetchall()
        return [{"rank": i + 1, "nick": r[0], "score": r[1]} for i, r in enumerate(rows)]
