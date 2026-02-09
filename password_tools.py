import hashlib

def hash_password(password):

    return hashlib.sha256(password.encode()).hexdigest() # Encode string to bytes because hash function requires that
                                                         # (CONT.) create SHA256 hash from bytes
                                                         # (CONT 2.) Convert hash into readable hexadecimal string


def verify_password(password, stored_hash):             # Function returns boolean whether hashed password equals the stored hash
    
    return hash_password(password) == stored_hash
    

