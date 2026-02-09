import sqlite3
from password_tools import hash_password
from database import get_connection, close_connection

# Connect to database
connection, cursor = get_connection()

# Function to add user into SQL database
# Will return string if there's an error, None if success
def send_register_request(username, password):

    try:
        password_hash = hash_password(password)     # Get hashed password to store in database

        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash)) # ? ? are placeholder values and we specify after
        close_connection(connection)

        return None     # Success there was no error to catch
    
    except sqlite3.IntegrityError:
        # This is the error we catch if UNIQUE identify fails because username already exists
        return "* Username already in use."
    
    except Exception:
        # For any other exceptions
        return "* Something went wrong. Please try again."

# def send_login_request(username, password):


