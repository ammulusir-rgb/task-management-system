import psycopg

# Connect to existing database first
conn = psycopg.connect("host=127.0.0.1 port=5432 user=postgres password=password dbname=vector_db")
conn.autocommit = True
cur = conn.cursor()

cur.execute("SELECT version()")
print("PG Connected:", cur.fetchone()[0][:60], flush=True)

# Check/create taskmanager database
cur.execute("SELECT datname FROM pg_database WHERE datname='taskmanager'")
if cur.fetchone():
    print("Database 'taskmanager' already exists", flush=True)
else:
    cur.execute("CREATE DATABASE taskmanager")
    print("Database 'taskmanager' created", flush=True)

conn.close()
print("DONE", flush=True)
