import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host="aws-1-ap-northeast-2.pooler.supabase.com",
        database="postgres",
        user="postgres.dftgrojbqvzfwgrtlyjh",  # COPY FULL USERNAME FROM SUPABASE
        password="ALLU1234chillu!",
        port=5432,
        sslmode="require"
    )
