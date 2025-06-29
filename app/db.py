import psycopg2

DB_CONFIG = {
    'host': 'db.xwmnvngocgcpcuxyzvwt.supabase.co',  # ✅ Correct host from your connection string
    'port': '5432',
    'database': 'postgres',
    'user': 'postgres',  # Confirmed from connection string
    'password': '6zwXcRqbu94m2zXD',  # Replace with your real password
    'sslmode': 'require'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)