import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

def create_database():
    try:
        # Connect to default 'postgres' database
        con = psycopg2.connect(
            dbname='postgres',
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432')
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        
        # Check if exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'essivi'")
        exists = cur.fetchone()
        
        if not exists:
            print("Creating database 'essivi'...")
            cur.execute('CREATE DATABASE essivi')
            print("Database created successfully.")
        else:
            print("Database 'essivi' already exists.")
            
        cur.close()
        con.close()
    except Exception as e:
        print(f"Error creating database: {e}")
        # Build failure is not fatal if we can't connect, user might need to intervene
        exit(1)

if __name__ == '__main__':
    create_database()
