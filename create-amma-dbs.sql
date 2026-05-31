SELECT 'CREATE DATABASE auth_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'auth_db')\gexec
SELECT 'CREATE DATABASE expense_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'expense_db')\gexec
SELECT 'CREATE DATABASE loan_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'loan_db')\gexec
SELECT 'CREATE DATABASE notification_db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'notification_db')\gexec
