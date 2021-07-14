CREATE TABLE IF NOT EXISTS tracking (
    user_id TEXT PRIMARY KEY,
    message_last_time INT,
    message_last_url TEXT
);
