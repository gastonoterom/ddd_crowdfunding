ACCOUNTING_AGGREGATE_DDL = """
    CREATE TABLE IF NOT EXISTS accounting_accounts (
        account_id VARCHAR PRIMARY KEY,
        deposits JSONB,
        withdrawals JSONB,
        version INT
    );
"""
