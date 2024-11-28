# read categories cache
import logging

import streamlit as st
import pandas as pd
from project.categories import (
    CategoriesCache,
    CategoriesRules,
    read_categories_rules,
)
from project.transactions_read import add_columns, parse_directory_as_df
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


@st.cache_data
def _read_all_transactions_raw() -> pd.DataFrame:
    log.info("Reading raw transactions from source files")
    df = parse_directory_as_df(TRANSACTIONS_FILES_DIR)
    log.info(f"Read {len(df)} raw transactions from source files")
    return df


categories_cache = CategoriesCache(file_path=CATEGORIES_CACHE_FILE_PATH)
categories_cache.read()

categories_rules = read_categories_rules(CATEGORIES_RULES_FILE_PATH)
all_categories = sorted(list(set([cr.category for cr in categories_rules.items])))

all_transactions_df = _add_columns_to_raw_transactions(
    _read_all_transactions_raw(), categories_rules, categories_cache
)
not_own_transactions_df = all_transactions_df[
    all_transactions_df['category'] != 'own-transfer'
]
