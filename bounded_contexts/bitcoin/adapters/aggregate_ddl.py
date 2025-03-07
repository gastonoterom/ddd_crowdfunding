BTC_INVOICES_AGGREGATE_DDL = """
    CREATE TABLE IF NOT EXISTS btc_invoices (
        payment_hash VARCHAR PRIMARY KEY,
        account_id VARCHAR,
        payment_request VARCHAR,
        invoice_type VARCHAR,
        amount INT,
        status VARCHAR
    );
    """
