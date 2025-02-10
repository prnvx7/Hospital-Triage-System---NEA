import hashlib      # Hashlib module used to implement SHA-256 hashing algorithm
import os           # OS module used to generate random salt

def hash_password(password: str) -> str:
    # Takes in the password as a string for argument, to return hash (salt + hashed password) as a string

    salt = os.urandom(16).hex()     # 16-byte random salt generated - converted to hexadecimal string
    hash_obj = hashlib.sha256((salt + password).encode('utf-8'))   # Combining salt and hashed password, encoded using UTF-8, hashed using SHA-256

    password_hash = hash_obj.hexdigest()        # converting hash object to a hexadecimal string

    return f"{salt}${password_hash}"   # salt and hash are separated using a $ sign

# Verifying whether the provided password matches the stored hash
def verify_password(stored_password: str, provided_password: str) -> bool:
    # Returns a boolean value (True or False) - True if password matches, False if password doesn't

    # Exception handling used to maintain code and ensure program runs without crashing
    try:
        salt, stored_hash = stored_password.split('$')      # splitting stored password into salt and hash

        # Recalculating the hash using SHA-256 and converting hashed object to hexadecimal string
        hash_obj = hashlib.sha256((salt + provided_password).encode('utf-8'))
        provided_hash = hash_obj.hexdigest()

        return provided_hash == stored_hash     # comparing provided hash to stored hash, returns True or False

    except Exception as e:
        print(f"Error during password verification: {e}")
        return False


'''# Test hashing algorithm using example password
stored_hash = hash_password("password_123")
print(f"Stored hash: {stored_hash}")

# Verification of hashing algorithm
verify_hash = verify_password(stored_hash, "password_123")
print(f"Password Match = {verify_hash}")


'''