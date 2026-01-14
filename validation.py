import requests
import re       # regular expressions

def run_validators(username, password):

    errors = []

    # if (self.__class__.__name__)
    # Get input values
    username = username.text().strip() # Need to use .strip() in case user adds spaces
    password = password.text().strip()

    # Check if username is blank, if not, continue checks: ==========================================
    if username:

        # Check username length lower bound
        if len(username) < 6:

            errors.append("* Username too short. Username must be between 6 and 24 characters long.")

        # Check username length upper bound
        if len(username) > 24:

            errors.append("* Username too long. Username must be between 6 and 24 characters long.")

        # Check if username contains invalid characters
        if not re.match(r'^[a-zA-Z0-9]+$', username):
            
            errors.append("* Username can only contain letters (A-Z, case insensitive) and numbers (0-9).")

    # If "if username" fails, this will run
    else:

        errors.append("* Username cannot be blank.")

    # ===============================================================================================

    if password:

        # Check password length lower bound
        if len(password) < 8: 

            errors.append("* Password too short. Password must be between 8 and 64 characters long.")

        # Check password length upper bound
        if len(password) > 64:

            errors.append("* Password too long. Password must be between 8 and 64 characters long.")

        # Check if password has at least 1 lowercase letter
        if not re.search(r'[a-z]', password):

            errors.append ("* Password must contain at least 1 lowercase letter.")

        # Check if password has at least 1 uppercase letter
        if not re.search(r'[A-Z]', password):

            errors.append ("* Password must contain at least 1 uppercase letter.")

        # Check if password has at least 1 number
        if not re.search(r'[0-9]', password):

            errors.append ("* Password must contain at least 1 number.")

        if not re.search(r'[~!@#$%^&*()\-\_=+\[\]{}|;:\'",<>\/?]', password):
        
            errors.append("* Password must contain at least one symbol. Acceptable symbols: ~!@#$%^&*()-_=+[]{}|;:'\",<>/?")

    else:

        errors.append("* Password cannot be blank.")

    return errors