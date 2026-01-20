SELECT 'CREATE DATABASE deribit' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'deribit')\gexec
