import os

DB_CONFIG = {
    "host": os.getenv(
        "DB_HOST",
        "ep-noisy-brook-b4eh2y4e-pooler.c-6.us-east-2.aws.neon.tech"
    ),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "neondb"),
    "user": os.getenv("DB_USER", "neondb_owner"),
    "password": os.getenv("DB_PASSWORD", ""),
    "sslmode": "require",
    "channel_binding": "require",
}

