CAMPAIGN_AGGREGATE_DDL = """
    CREATE TABLE IF NOT EXISTS campaigns (
        entity_id VARCHAR PRIMARY KEY,
        account_id VARCHAR,
        title VARCHAR,
        description VARCHAR,
        goal INT,
        total_raised INT,
        donations JSONB
    );
    """
