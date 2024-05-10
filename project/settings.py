import os

project_dir = os.path.dirname(os.path.dirname(__file__))
ROOT_INPUT_FILES_DIR = os.path.join(project_dir, "data")
TRANSACTIONS_FILES_DIR = os.path.join(ROOT_INPUT_FILES_DIR, "transactions")
CATEGORIES_RULES_FILE_PATH = os.path.join(
    ROOT_INPUT_FILES_DIR, "categories", "categories_conditions.csv"
)
CATEGORIES_CACHE_FILE_PATH = os.path.join(
    ROOT_INPUT_FILES_DIR, "categories", "categories_cache.csv"
) 