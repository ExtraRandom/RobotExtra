CREATE TABLE IF NOT EXISTS activity (
    db_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INT,
    server_id INT,
    message_last_time INT,
    message_last_url TEXT
)