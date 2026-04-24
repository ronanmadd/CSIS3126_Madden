import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'spectrasync_data.db')       # file extension is .db for sqlite usually

# Function returns connection and cursor to database
def get_connection():

    # try-except for if connection fails?

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

    # Create a table (if it doesn't exist) for users 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            default_mode TEXT NOT NULL DEFAULT 'Solid',
            default_brightness INTEGER NOT NULL DEFAULT 128,
            remember_session INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')                                     # Triple quotes (''') good for writing multiline strings without \n

    close_connection(connection)

# Function to create default settings row for user
def create_default_settings(user_id):
    connection, cursor = get_connection()

    # "INSERT OR IGNORE", skip it instead of erroring if user already has settings
    cursor.execute('''
        INSERT OR IGNORE INTO user_settings (user_id, default_mode, default_brightness, remember_session)
        VALUES (?, 'Solid', 128, 0)
    ''', (user_id,))

    close_connection(connection)

# Function to look up user's numeric ID from username
def get_user_id(username):
    connection, cursor = get_connection()

    # cursor.fetchone() grabs the first matching row
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()

    connection.close()

    # Return the ID if found, else return None
    if row:
        return row[0] 
    else: 
        return None

# Create function to load user settings
def get_user_settings(user_id):
    connection, cursor = get_connection()

    # Get users saved mode, brightness, and remember setting
    cursor.execute('''
        SELECT default_mode, default_brightness, remember_session
        FROM user_settings
        WHERE user_id = ?
    ''', (user_id,))
    row = cursor.fetchone()                                     # Reads in the matching row

    connection.close()

    # If the settings row doesn't exist yet, just return default values instead
    if row is None:
        return {
            "default_mode": "Solid",
            "default_brightness": 128,
            "remember_session": 0
        }

    # Else, if row exists, return values in dict form
    return {
        "default_mode": row[0],
        "default_brightness": row[1],
        "remember_session": row[2]
    }

# Create function to save user settings
def save_user_settings(user_id, default_mode, default_brightness, remember_session):
    connection, cursor = get_connection()

    # If user has no settings row, insert one
    # (CONT.) if  they already have one, update it
    # (CONT. 2) if they already have one then ON CONFLICT will trigger because user_id is unique, so then it will update instead
    # (CONT. 3) "excluded" is saying update the existing row using the values from the failed insert
    cursor.execute('''
        INSERT INTO user_settings (user_id, default_mode, default_brightness, remember_session)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            default_mode = excluded.default_mode,
            default_brightness = excluded.default_brightness,
            remember_session = excluded.remember_session
    ''', (user_id, default_mode, default_brightness, remember_session))

    close_connection(connection)

# Function to clear remembered login for everyone (only one person should be remembered at a time)
def clear_remembered_users():
    connection, cursor = get_connection()

    # Sets all remember_session values to 0
    cursor.execute("UPDATE user_settings SET remember_session = 0")

    close_connection(connection)

# Function to find which user is remembered
def get_remembered_user():
    connection, cursor = get_connection()

    # Joins users and user_settings so it can find which user has remember_session = 1, and returns that username
    # (CONT.) The JOIN line says match rows from users and user_settings where users.id == user_settings.user_id, user_settings doesn't have username and users doesn't have remember_session
    cursor.execute('''
        SELECT users.username
        FROM users
        JOIN user_settings ON users.id = user_settings.user_id
        WHERE user_settings.remember_session = 1
        LIMIT 1
    ''')
    # Read in matching row
    row = cursor.fetchone()

    connection.close()

    # Return the username if found, otherwise return None
    if row:
        return row[0] 
    else:
        return None