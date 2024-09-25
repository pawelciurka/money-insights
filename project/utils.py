import hashlib
import os


def hash_string(string: str) -> str:
    # Create a hash object
    hash_object = hashlib.sha256()
    # Update the hash object with the string's bytes
    hash_object.update(string.encode())
    # Get the hexadecimal representation of the hash
    hash_hex = hash_object.hexdigest()
    return hash_hex


def calculate_md5(file_path: str) -> str:
    hash_md5 = hashlib.md5()

    # Open file in binary mode
    with open(file_path, "rb") as f:
        # Read and update the hash in chunks of 4KB
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    # Return the hexadecimal MD5 hash
    return hash_md5.hexdigest()


def list_files(directory: str) -> list[str]:
    file_list = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_list.append(os.path.join(root, file))

    return file_list


def get_emoji(category_name: str):
    return {"groceries": "🛒", "income": "🔺", "outcome": "🔻"}.get(category_name, "")
