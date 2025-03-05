AUTH_ACCOUNT_DDL = """
    CREATE TABLE IF NOT EXISTS auth_accounts (
        account_id VARCHAR PRIMARY KEY,
        username VARCHAR NOT NULL UNIQUE,
        password VARCHAR NOT NULL
    );
"""
