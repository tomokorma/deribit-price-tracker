CREATE DATABASE deribit;

\c deribit;

CREATE TABLE price_ticks (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    price FLOAT NOT NULL,
    timestamp INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ticker ON price_ticks(ticker);
CREATE INDEX idx_timestamp ON price_ticks(timestamp);
CREATE INDEX idx_ticker_timestamp ON price_ticks(ticker, timestamp);

GRANT ALL PRIVILEGES ON TABLE price_ticks TO postgres;
GRANT USAGE, SELECT ON SEQUENCE price_ticks_id_seq TO postgres;

DO $$
BEGIN
    RAISE NOTICE 'Database deribit and table price_ticks created successfully';
END $$;
