import sqlite3




def create_database_user():
    """
    Creates a database to store packet details.
    """
    conn = sqlite3.connect("Users.db",check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          cnic TEXT UNIQUE NOT NULL, 
          pass TEXT NOT NULL,
          ref_name TEXT,
          remarks TEXT,
          email TEXT,
          phno TEXT,
          CONSTRAINT cnic_format CHECK (LENGTH(cnic) = 13 AND cnic GLOB '[0-9]*'), 
          CONSTRAINT email_format CHECK (
              email LIKE '%_@_%._%' AND
              LENGTH(email) > 5
          )
    )
""")
    conn.commit()
    return conn , cursor



def create_database_file():
    """
    Creates a database to store packet details.
    """
    conn = sqlite3.connect("Files.db",check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
          CREATE TABLE IF NOT EXISTS files (
          id INTEGER ,
          name VARCHAR(255) ,
          file_data LONGBLOB 
                
        )
""")
    conn.commit()
    return conn , cursor
