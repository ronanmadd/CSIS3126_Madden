import sqlite3

DATABASE_PATH = 'spectrasync_data.db'       # file extension is .db for sqlite usually

# Function returns connection and cursor to database
def get_connection():

    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.cursor()            # Cursor manages interactions with DB, serves as bridge between app and DB
                                            # (CONT.) primarliy to execute SQL statements and traverse rows 1 at a time

    return connection, cursor

# Function commits changes and closes connection
def close_connection(connection):

    connection.commit()                     # Basically like saving your changes, similiar to GitHub commit
    connection.close()

# Create a table (if it doesn't exist) for users with a unique username and a field for the hashed password
def create_database():
    connection, cursor = get_connection()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    ''')                                    # Triple quotes (''') good for writing multiline strings without \n

    close_connection(connection)

