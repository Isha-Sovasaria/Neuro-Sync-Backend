from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

def get_connection():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not found in environment variables")
    
    try:
        return psycopg2.connect(database_url)
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise

def test_connection():
    try:
        conn = get_connection()
        print("Supabase connection successful!")
        conn.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
