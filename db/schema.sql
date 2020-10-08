CREATE TABLE IF NOT EXISTS tracking (
    user_id STRING PRIMARY KEY,
    message_last_time INT,
    message_last_url STRING
);
