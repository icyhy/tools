import sqlite3

def upgrade_db():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    try:
        print("Adding custom_plugins column to events table...")
        cursor.execute("ALTER TABLE events ADD COLUMN custom_plugins JSON")
        print("Success.")
    except sqlite3.OperationalError as e:
        print(f"Skipping events update: {e}")
        
    try:
        print("Adding interaction_count column to participants table...")
        cursor.execute("ALTER TABLE participants ADD COLUMN interaction_count INTEGER DEFAULT 0")
        print("Success.")
    except sqlite3.OperationalError as e:
        print(f"Skipping participants update: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    upgrade_db()
