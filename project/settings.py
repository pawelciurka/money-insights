import os
import shutil
from pathlib import Path
from project.constants import (
    ROOT_INPUT_FILES_DIR,
    ROOT_EXAMPLE_INPUT_FILES_DIR,
    TRANSACTIONS_FILES_DIR,
    CATEGORIES_CACHE_FILE_PATH,
    CATEGORIES_RULES_FILE_PATH,
)

if not os.path.isdir(ROOT_INPUT_FILES_DIR):
    os.makedirs(os.path.join(ROOT_INPUT_FILES_DIR, "transactions", "generic"))
    shutil.copy(
        os.path.join(
            ROOT_EXAMPLE_INPUT_FILES_DIR,
            "transactions",
            "generic",
            "fake_transactions.csv",
        ),
        os.path.join(
            ROOT_INPUT_FILES_DIR, "transactions", "generic", "fake_transactions.csv"
        ),
    )

    os.makedirs(os.path.join(ROOT_INPUT_FILES_DIR, "categories"))
    shutil.copy(
        os.path.join(
            ROOT_EXAMPLE_INPUT_FILES_DIR,
            "categories",
            "categories_conditions.csv",
        ),
        os.path.join(ROOT_INPUT_FILES_DIR, "categories", "categories_conditions.csv"),
    )

os.makedirs(TRANSACTIONS_FILES_DIR, exist_ok=True)
os.makedirs(Path(CATEGORIES_RULES_FILE_PATH).parent, exist_ok=True)
os.makedirs(Path(CATEGORIES_CACHE_FILE_PATH).parent, exist_ok=True)
