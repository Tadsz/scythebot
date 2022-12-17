CREATE_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS chat_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        created_at DATETIME,
        prompt TEXT,
        prompt_history TEXT,
        prompt_response TEXT,
        input_tokens INT,
        output_tokens INT,
        max_tokens INT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """,
]
