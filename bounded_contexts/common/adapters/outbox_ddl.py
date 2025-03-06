OUTBOX_DDL = """
    CREATE TABLE IF NOT EXISTS outbox_messages (
        message_id varchar PRIMARY KEY,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        message_data bytea NOT NULL
    );
"""
