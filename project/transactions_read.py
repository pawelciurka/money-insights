from argparse import Namespace
from dataclasses import dataclass
from datetime import timedelta
import os
from types import SimpleNamespace
import numpy as np
import pandas as pd
import unicodedata
import codecs
from io import StringIO
from enum import Enum
import logging
import re
from project.categories import CategoriesCache, CategoriesRules, CategoryRule

from project.utils import hash_string, list_files
import streamlit as st

log = logging.getLogger(__name__)


@dataclass
class CsvCol:
    index: int
    name: str


class SourceType(Enum):
    ing = 1
    mbank = 2
    generic = 3


@dataclass
class CsvFile:
    path: str
    source_type: SourceType


TRANSACTION_COLUMNS = SimpleNamespace(
    TRANSACTION_DATE='transaction_date',
    CONTRACTOR='contractor',
    TITLE='title',
    TRANSACTION_ID='transaction_id',
    AMOUNT='amount',
    ACCOUNT_NAME='account_name',
    SOURCE_FILE_PATH="source_file_path",
)

input_cols_ing: list[CsvCol] = [
    CsvCol(0, TRANSACTION_COLUMNS.TRANSACTION_DATE),
    CsvCol(2, TRANSACTION_COLUMNS.CONTRACTOR),
    CsvCol(3, TRANSACTION_COLUMNS.TITLE),
    CsvCol(7, TRANSACTION_COLUMNS.TRANSACTION_ID),
    CsvCol(8, TRANSACTION_COLUMNS.AMOUNT),
    CsvCol(14, TRANSACTION_COLUMNS.ACCOUNT_NAME),
]
input_cols_mbank: list[CsvCol] = [
    CsvCol(0, TRANSACTION_COLUMNS.TRANSACTION_DATE),
    CsvCol(3, TRANSACTION_COLUMNS.TITLE),
    CsvCol(4, TRANSACTION_COLUMNS.CONTRACTOR),
    CsvCol(6, TRANSACTION_COLUMNS.AMOUNT),
]

mandatory_out_fields = {
    TRANSACTION_COLUMNS.TRANSACTION_DATE,
    TRANSACTION_COLUMNS.CONTRACTOR,
    TRANSACTION_COLUMNS.TRANSACTION_ID,
    TRANSACTION_COLUMNS.TITLE,
    TRANSACTION_COLUMNS.AMOUNT,
    TRANSACTION_COLUMNS.ACCOUNT_NAME,
    TRANSACTION_COLUMNS.SOURCE_FILE_PATH,
}


class Parser:
    @staticmethod
    def normalize_lines(lines):
        return [
            unicodedata.normalize("NFD", line).encode("ascii", "ignore")
            for line in lines
        ]

    @staticmethod
    def validate_raw(df) -> str:
        missing_fields = mandatory_out_fields - set(df.keys())
        err = ""
        if missing_fields:
            err += f"Missing fields: {missing_fields}"
        return err

    @staticmethod
    def convert_transaction_date(transaction_date: pd.Series) -> pd.Series:
        return pd.to_datetime(transaction_date) + timedelta(minutes=1)

    def parse_raw(self, file_path: str):
        raise NotImplementedError()

    @staticmethod
    def clean_raw(df):
        df["title"] = df["title"].astype(str)
        df["contractor"] = df["contractor"].astype(str)
        df["transaction_date"] = Parser.convert_transaction_date(df["transaction_date"])
        return df

    def parse_and_validate(self, file_path: str) -> pd.DataFrame:
        df = self.parse_raw(file_path)
        df[TRANSACTION_COLUMNS.SOURCE_FILE_PATH] = file_path
        df = self.clean_raw(df)
        err = self.validate_raw(df)

        if err:
            raise AssertionError(err)

        # filters
        df = df[~df["amount"].isna()]

        return df


class IngParser(Parser):
    @staticmethod
    def truncate_header(lines: list[bytes]):
        for i_line, line in enumerate(lines):
            if line.startswith(b'''"Data transakcji"'''):
                i_header_line = i_line
                break

        return lines[i_header_line + 1 :]

    @staticmethod
    def truncate_footer(lines: list[bytes]):
        i_footer_line = len(lines)
        for i_line, line in enumerate(lines):
            if line.startswith(b""""Dokument ma charakter informacyjny"""):
                i_footer_line = i_line
                break

        return lines[:i_footer_line]

    def parse_raw(self, file_path) -> pd.DataFrame:
        with codecs.open(file_path, "rb", "cp1250") as f:
            lines = f.readlines()
            lines_n = self.normalize_lines(lines)
            lines_nth = self.truncate_header(lines_n)
            lines_ntf = self.truncate_footer(lines_nth)

        string_io = StringIO(b"".join(lines_ntf).decode("utf-8"))

        # read as dataframe
        df = pd.read_csv(
            string_io,
            header=None,
            sep=";",
            usecols=[ic.index for ic in input_cols_ing],
            names=[ic.name for ic in input_cols_ing],
        )

        return df


class MbankParser(Parser):
    @staticmethod
    def truncate_header(lines: list[bytes]) -> list[bytes]:
        for i_line, line in enumerate(lines):
            if line.startswith(b"#Data ksiegowania"):
                i_header_line = i_line
                break

        return lines[i_header_line + 1 :]

    @staticmethod
    def truncate_footer(lines: list[bytes]) -> list[bytes]:
        i_footer_line = len(lines)
        for i_line, line in enumerate(lines):
            if b"#Saldo" in line:
                i_footer_line = i_line
                break

        return lines[:i_footer_line]

    def parse_raw(self, file_path: str) -> pd.DataFrame:
        with codecs.open(file_path, "rb", "cp1250") as f:
            lines = f.readlines()
            lines_n = self.normalize_lines(lines)
            lines_nt = self.truncate_header(lines_n)
            lines_ntf = self.truncate_footer(lines_nt)

        string_io = StringIO(b"".join(lines_ntf).decode("utf-8"))

        # read as dataframe
        df = pd.read_csv(
            string_io,
            sep=";",
            header=None,
            usecols=[ic.index for ic in input_cols_mbank],
            names=[ic.name for ic in input_cols_mbank],
        )

        df["transaction_id"] = df.apply(
            lambda r: hash_string("".join([str(v) for v in r])), axis=1
        )
        df["account_name"] = "mbank"

        return df


class GenericParser(Parser):
    def parse_raw(self, file_path: str) -> pd.DataFrame:
        df = pd.read_csv(
            file_path,
            sep=',',
            usecols=mandatory_out_fields,
        )
        return df


PARSER_BY_SOURCE_TYPE: dict[str, type] = {
    SourceType.ing.name: IngParser,
    SourceType.mbank.name: MbankParser,
    SourceType.generic.name: GenericParser,
}


@st.cache_data
def parse_csv_files_as_df(csv_files: list[CsvFile]) -> pd.DataFrame:
    dfs = []
    for csv_file in csv_files:
        log.info(f"Parsing {csv_file}")
        parser = PARSER_BY_SOURCE_TYPE[csv_file.source_type.name]()
        df = parser.parse_and_validate(csv_file.path)
        log.info(f"{len(df)} transaction read from {csv_file.path}")
        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)
    return df


def parse_directory_as_df(root_input_files_dir) -> pd.DataFrame:
    """
    Example directories structure:
    <ROOT_INPUT_FILES_DIR>/ing/file_1.csv
    <ROOT_INPUT_FILES_DIR>/ing/file_2.csv
    <ROOT_INPUT_FILES_DIR>/mbank/file_1.csv
    """
    csv_files = []
    for source_type in list(SourceType):
        single_source_dir = os.path.join(root_input_files_dir, source_type.name)
        if not os.path.isdir(single_source_dir):
            log.warning(
                f"directory for source of type {source_type.name} not found (expected: {single_source_dir})"
            )
            continue

        file_names = list_files(single_source_dir)

        for file_name in file_names:
            file_path = os.path.join(single_source_dir, file_name)
            if not file_name.lower().endswith(".csv"):
                continue
            csv_files.append(CsvFile(file_path, source_type))

    if len(csv_files) == 0:
        msg = f"No input files discovered in {root_input_files_dir}"
        raise ValueError(msg)

    return parse_csv_files_as_df(csv_files)


def get_category(
    row: pd.Series, categories_rules: list[CategoryRule]
) -> CategoryRule | None:
    for category_rule in categories_rules:
        is_match = all(
            [
                condition.evaluate(row[condition.column])
                for condition in category_rule.conditions
            ]
        )
        if is_match:
            return category_rule
    return None


def add_columns(
    df: pd.DataFrame,
    categories_rules: CategoriesRules,
    categories_cache: CategoriesCache,
) -> pd.DataFrame:
    df = df.copy()
    df["transaction_date"] = df["transaction_date"].map(lambda d: pd.to_datetime(d))
    df["transaction_date_isostr"] = df["transaction_date"].map(
        lambda d: d.strftime("%Y-%m-%d")
    )

    df["amount"] = df["amount"].map(
        lambda x: float(re.sub("(PLN)", "", str(x)).replace(" ", "").replace(",", "."))
    )
    df["type"] = df["amount"].map(lambda x: "income" if x >= 0 else "outcome")
    df["amount_abs"] = df["amount"].map(lambda x: abs(x))
    df["one_group"] = "all"

    log.info("Setting categories")
    n_recomputed_transactions = 0
    n_read_from_cache = 0

    categories_data = []
    for i, transaction in df.iterrows():
        category, category_rule_id = categories_cache.get(
            transaction["transaction_id"],
            ("unrecognized", np.NaN),
        )

        if np.isnan(category_rule_id):
            n_recomputed_transactions += 1
            category_rule = get_category(transaction, categories_rules.items)

            if category_rule:
                category, category_rule_id = (
                    category_rule.category,
                    category_rule.rule_id,
                )
            else:
                category, category_rule_id = "unrecognized", None
        else:
            n_read_from_cache += 1

        categories_data.append(
            {
                'index': i,
                'category': category,
                'category_rule_id': category_rule_id,
            }
        )
    log.info("Joining")
    df = df.join(pd.DataFrame(categories_data).set_index('index'))

    log.info(f"Categories recomputed: {n_recomputed_transactions}")
    log.info(f"Categories read from cache: {n_read_from_cache}")

    categories_cache.write(df)

    return df
