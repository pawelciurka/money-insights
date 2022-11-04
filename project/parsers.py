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
    CsvCol(7, "transaction_id"),
    CsvCol(8, "amount"),
    CsvCol(14, "account_name"),
]
input_cols_mbank: list[CsvCol] = [
    CsvCol(0, "transaction_date"),
    CsvCol(4, "contractor"),
    CsvCol(6, "amount"),
]

mandatory_out_fields = {
    "transaction_date",
    "contractor",
    "transaction_id",
    "amount",
    "account_name",
    "type",
    "amount_abs",
    "one_group",
}


class Parser:
    @staticmethod
    def normalize_lines(lines):
        return [
            unicodedata.normalize("NFD", line).encode("ascii", "ignore")
            for line in lines
        ]

    @staticmethod
    def validate(df) -> str:
        missing_fields = mandatory_out_fields - set(df.keys())
        err = ""
        if missing_fields:
            err += f"Missing fields: {missing_fields}"
        return err

    @staticmethod
    def convert_transaction_date(transaction_date: pd.Series) -> pd.Series:
        return pd.to_datetime(transaction_date) + timedelta(minutes=1)

    @staticmethod
    def convert_amount(amount: pd.Series) -> pd.Series:
        return amount.map(
            lambda x: float(
                re.sub("(PLN)", "", str(x)).replace(" ", "").replace(",", ".")
            )
        )

    @staticmethod
    def get_type(amount: pd.Series) -> pd.Series:
        return amount.map(lambda x: "income" if x >= 0 else "outcome")

    @staticmethod
    def get_amount_abs(amount: pd.Series) -> pd.Series:
        return amount.map(lambda x: abs(x))

    @staticmethod
    def get_one_group():
        return "all"

    def parse(self, file_path: str):
        raise NotImplementedError()

    def parse_and_validate(self, file_path: str) -> pd.DataFrame:
        df = self.parse(file_path)
        err = self.validate(df)
        if err:
            raise AssertionError(err)
        else:
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

    def parse(self, file_path) -> pd.DataFrame:
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

        # translate
        df["transaction_date"] = self.convert_transaction_date(df["transaction_date"])
        df["amount"] = self.convert_amount(df["amount"])

        # add columns
        df["type"] = self.get_type(df["amount"])
        df["amount_abs"] = self.get_amount_abs(df["amount"])
        df["one_group"] = self.get_one_group()

        # filters
        df = df[~df["amount"].isna()]

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

    def parse(self, file_path: str) -> pd.DataFrame:
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

        # translate
        df["transaction_date"] = self.convert_transaction_date(df["transaction_date"])
        df["amount"] = self.convert_amount(df["amount"])

        # add columns
        df["type"] = self.get_type(df["amount"])
        df["amount_abs"] = self.get_amount_abs(df["amount"])
        df["one_group"] = self.get_one_group()
        df["transaction_id"] = "unknown"  #
        df["account_name"] = "mbank"

        # filters
        df = df[~df["amount"].isna()]

        return df


PARSER_BY_SOURCE_TYPE: dict[str, Parser] = {
    SourceType.ing.name: IngParser(),
    SourceType.mbank.name: MbankParser(),
}


def parse_csv_files_as_df(csv_files: list[CsvFile]) -> pd.DataFrame:
    dfs = []
    for csv_file in csv_files:
        log.info(f"Parsing {csv_file}")
        parser = PARSER_BY_SOURCE_TYPE[csv_file.source_type.name]
        dfs.append(parser.parse_and_validate(csv_file.path))

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
                f"directory for source of type {source.name} not found (expected: {single_source_dir})"
            )
            continue

        file_names = os.listdir(single_source_dir)

        for file_name in file_names:
            file_path = os.path.join(single_source_dir, file_name)
            csv_files.append(CsvFile(file_path, source_type))

    if len(csv_files) == 0:
        msg = f"No input files discovered in {root_input_files_dir}"
        raise ValueError(msg)

    return parse_csv_files_as_df(csv_files)
