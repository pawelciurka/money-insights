from dataclasses import dataclass
from datetime import timedelta
import os
import pandas as pd
import unicodedata
import codecs
from io import StringIO
from enum import Enum
import logging
import re

log = logging.getLogger(__name__)


@dataclass
class CsvCol:
    index: int
    name: str


class SourceType(Enum):
    ing = 1
    mbank = 2


@dataclass
class CsvFile:
    path: str
    source_type: SourceType


input_cols_ing: list[CsvCol] = [
    CsvCol(0, "transaction_date"),
    CsvCol(2, "contractor"),
    CsvCol(3, "title"),
    CsvCol(7, "transaction_id"),
    CsvCol(8, "amount"),
    CsvCol(14, "account_name"),
]
input_cols_mbank: list[CsvCol] = [
    CsvCol(0, "transaction_date"),
    CsvCol(3, "title"),
    CsvCol(4, "contractor"),
    CsvCol(6, "amount"),
]

mandatory_out_fields = {
    "transaction_date",
    "contractor",
    "transaction_id",
    "title",
    "amount",
    "account_name",
}

categories_definitions_cols = ["rule_id", "column", "relation", "value", "category"]


class Relation(Enum):
    equals = 1
    contains = 2


@dataclass
class Condition:
    column: str
    relation: Relation
    value: str

    def evaluate(self, other: str):
        def equals(other):
            return str(other) == self.value

        def contains(other: str):
            return self.value in str(other)

        return {"equals": equals, "contains": contains}[self.relation.name](other)


@dataclass
class CategoryRule:
    category: str
    contitions: list[Condition]


def read_categories_rules(categories_csv_path: str) -> list[CategoryRule]:
    log.info(f"Reading categories from {categories_csv_path}")
    df = pd.read_csv(categories_csv_path, usecols=categories_definitions_cols)

    categories_rules = []
    for rule_id, rule_conditions_df in df.groupby("rule_id"):
        if len(set(rule_conditions_df["category"])) != 1:
            raise AssertionError(
                f"Categories for rule {rule_id} differ between conditions!"
            )

        category = rule_conditions_df["category"].iloc[0]
        rule_conditions = []
        for _, condition in rule_conditions_df.iterrows():
            rule_conditions.append(
                Condition(
                    column=condition["column"],
                    relation=Relation[condition["relation"]],
                    value=condition["value"],
                )
            )

        categories_rules.append(
            CategoryRule(category=category, contitions=rule_conditions)
        )

    return categories_rules


class Parser:
    def __init__(self, categories_rules) -> None:
        self.categories_rules = categories_rules

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

    @staticmethod
    def get_category(row: pd.Series, categories_rules: list[CategoryRule]):
        for category_rule in categories_rules:
            is_match = all(
                [
                    condition.evaluate(row[condition.column])
                    for condition in category_rule.contitions
                ]
            )
            if is_match:
                return category_rule.category
        return "unrecognized"

    def parse_raw(self, file_path: str):
        raise NotImplementedError()

    def add_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df["transaction_date"] = df["transaction_date"].map(
            lambda d: pd.to_datetime(d) + timedelta(minutes=1)
        )
        df["amount"] = df["amount"].map(
            lambda x: float(
                re.sub("(PLN)", "", str(x)).replace(" ", "").replace(",", ".")
            )
        )
        df["type"] = df["amount"].map(lambda x: "income" if x >= 0 else "outcome")
        df["amount_abs"] = df["amount"].map(lambda x: abs(x))
        df["one_group"] = "all"
        df["category"] = df.apply(
            self.get_category, args=(self.categories_rules,), axis=1
        )

        return df

    @staticmethod
    def clean_raw(df):
        df["title"] = df["title"].astype(str)
        df["contractor"] = df["contractor"].astype(str)
        return df

    def parse_and_validate(self, file_path: str) -> pd.DataFrame:
        df = self.parse_raw(file_path)
        df = self.clean_raw(df)
        err = self.validate_raw(df)

        if err:
            raise AssertionError(err)

        df = self.add_columns(df)

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
            if line.startswith(b"#Data operacji;"):
                i_header_line = i_line
                break

        return lines[i_header_line + 1 :]

    @staticmethod
    def truncate_footer(lines: list[bytes]) -> list[bytes]:
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

        df["transaction_id"] = "unknown"
        df["account_name"] = "mbank"

        return df


PARSER_BY_SOURCE_TYPE: dict[str, type] = {
    SourceType.ing.name: IngParser,
    SourceType.mbank.name: MbankParser,
}


def parse_csv_files_as_df(
    csv_files: list[CsvFile], categories_rules_file_path: str
) -> pd.DataFrame:
    categories_rules = read_categories_rules(categories_rules_file_path)
    dfs = []
    for csv_file in csv_files:
        log.info(f"Parsing {csv_file}")
        parser = PARSER_BY_SOURCE_TYPE[csv_file.source_type.name](categories_rules)
        dfs.append(parser.parse_and_validate(csv_file.path))

    df = pd.concat(dfs, ignore_index=True)
    return df


def parse_directory_as_df(
    root_input_files_dir, categories_rules_file_path
) -> pd.DataFrame:
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

        file_names = os.listdir(single_source_dir)

        for file_name in file_names:
            file_path = os.path.join(single_source_dir, file_name)
            csv_files.append(CsvFile(file_path, source_type))

    if len(csv_files) == 0:
        msg = f"No input files discovered in {root_input_files_dir}"
        raise ValueError(msg)

    return parse_csv_files_as_df(csv_files, categories_rules_file_path)
