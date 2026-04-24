import sqlite3
from password_tools import hash_password, verify_password
from database import get_connection, close_connection, create_default_settings

# Function to add user into SQL database
# Will return string if there's an error, None if success
def send_register_request(username, password):

    # Connect to database
    connection, cursor = get_connection()

    try:
        password_hash = hash_password(password)     # Get hashed password to store in database

        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash)) # ? ? are placeholder values and we specify after

        user_id = cursor.lastrowid                  # Gets the id of the user just inserted

        connection.commit()                         # Commit change

        create_default_settings(user_id)            # Creates matching default row in user_settings for this new user

        return None     # Success there was no error to catch
    
    except sqlite3.IntegrityError:
        # This is the error we catch if UNIQUE identify fails because username already exists
        return "* Username already in use."
    
    except Exception:
        # For any other exceptions
        return "* Something went wrong. Please try again."
    
    finally:
        connection.close()

def send_login_request(username, password):
    connection, cursor = get_connection()

    try:
        # Look up the stored hash for this username
        cursor.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()

        # If username not found
        if row is None:
            return "* Invalid username or password."

        stored_hash = row[0]

        # Verify password against stored hash
        if not verify_password(password, stored_hash):
            return "* Invalid username or password."

        return None  # Success

    #except Exception:
    #    return "* Something went wrong. Please try again."

    except Exception as e:
        print("LOGIN ERROR:", repr(e))
        return f"* Something went wrong: {e}"

    finally:
        connection.close()


