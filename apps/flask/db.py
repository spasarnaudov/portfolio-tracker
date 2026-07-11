import psycopg

from config import DATABASE_CONFIG


def get_connection():
    if isinstance(DATABASE_CONFIG, str):
        return psycopg.connect(DATABASE_CONFIG)

    return psycopg.connect(**DATABASE_CONFIG)
