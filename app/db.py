import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'database': 'neuronsync',
    'user': 'postgres',           
    'password': 'isha1234',          
    'port': '5432'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)