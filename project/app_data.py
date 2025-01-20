import logging

import streamlit as st
import pandas as pd
from project.categories import (
    CategoriesCache,
    CategoriesRules,
    read_categories_rules,
)
from project.transactions_read import (
    add_columns,
    discover_csv_files,
    parse_csv_files_as_df,
)
from project.settings import (
    CATEGORIES_CACHE_FILE_PATH,
    CATEGORIES_RULES_FILE_PATH,
    TRANSACTIONS_FILES_DIR,
)


log = logging.getLogger(__name__)


@st.cache_data
def _add_columns_to_raw_transactions(
    transactions_raw_df: pd.DataFrame,
    categories_rules: CategoriesRules,
    categories_cache: CategoriesCache,
):
    log.info("adding columns")
    return add_columns(transactions_raw_df, categories_rules, categories_cache)


def _read_all_transactions_raw() -> pd.DataFrame:
    log.info("Reading raw transactions from source files")
    csv_files = discover_csv_files(TRANSACTIONS_FILES_DIR)
    df = parse_csv_files_as_df(csv_files)
    log.info(f"Read {len(df)} raw transactions from source files")
    return df


def read_fresh_data():
    categories_cache = CategoriesCache(file_path=CATEGORIES_CACHE_FILE_PATH)
    categories_cache.read()

    categories_rules = read_categories_rules(
        CATEGORIES_RULES_FILE_PATH, add_fallback=True
    )
    all_categories = sorted(list(set([cr.category for cr in categories_rules.items])))

    all_transactions_raw_df = _read_all_transactions_raw()

    all_transactions_df = _add_columns_to_raw_transactions(
        all_transactions_raw_df, categories_rules, categories_cache
    )

    return all_categories, all_transactions_df
