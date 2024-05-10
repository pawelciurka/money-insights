import hashlib


def hash_string(string: str):
    # Create a hash object
    hash_object = hashlib.sha256()
    # Update the hash object with the string's bytes
    hash_object.update(string.encode())
    # Get the hexadecimal representation of the hash
    hash_hex = hash_object.hexdigest()
    return hash_hex