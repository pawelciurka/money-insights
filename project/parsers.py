from dataclasses import dataclass
from datetime import date
import os
import plotly.figure_factory
import pandas as pd
import unicodedata
import codecs
from io import StringIO
from enum import Enum
import logging

from .settings import ROOT_INPUT_FILES_DIR

log = logging.getLogger(__name__)


@dataclass
class CsvCol:
    index: int
    name: str


class Source(Enum):
    ing = 1
    mbank = 2


@dataclass
class CsvFile:
    path: str
    source: Source


input_cols_ing: list[CsvCol] = [
    CsvCol(0, "transaction_date"),
    CsvCol(2, "contrctor"),
    CsvCol(3, "title"),
    CsvCol(7, "transaction_id"),
    CsvCol(8, "amount"),
    CsvCol(14, "account_name"),
]


class Parser:
    def parse(self, file_path) -> pd.DataFrame:
        csv_str = self.input_to_string_io(file_path)

        # read as dataframe
        df = pd.read_csv(csv_str, **self.read_csv_kwargs)

        # translate
        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        df["amount"] = df["amount"].map(lambda x: float(str(x).replace(",", ".")))

        # add columns
        df["type"] = df["amount"].map(lambda x: "income" if x >= 0 else "outcome")
        df["amount_abs"] = df["amount"].map(lambda x: abs(x))

        return df


class IngParser(Parser):
    read_csv_kwargs = dict(
        sep=";",
        header=None,
        usecols=[ic.index for ic in input_cols_ing],
        names=[ic.name for ic in input_cols_ing],
        dtype={"amount": str, "transaction_date": str},
    )

    @staticmethod
    def normalize_lines(lines):
        return [
            unicodedata.normalize("NFD", line).encode("ascii", "ignore")
            for line in lines
        ]

    @staticmethod
    def truncate_header(lines: list[str]):
        for i_line, line in enumerate(lines):
            if line.startswith(b'''"Data transakcji"'''):
                i_header_line = i_line
                break

        return lines[i_header_line + 1 :]

    @staticmethod
    def truncate_footer(lines: list[str]):
        i_footer_line = len(lines)
        for i_line, line in enumerate(lines):
            if line.startswith(b""""Dokument ma charakter informacyjny"""):
                i_footer_line = i_line
                break

        return lines[:i_footer_line]

    def input_to_string_io(self, file_path: str) -> StringIO:
        with codecs.open(file_path, "rb", "cp1250") as f:
            lines = f.readlines()
            lines_n = self.normalize_lines(lines)
            lines_nth = self.truncate_header(lines_n)
            lines_ntf = self.truncate_footer(lines_nth)

        string_io = StringIO(b"".join(lines_ntf).decode("utf-8"))
        return string_io


PARSER_BY_SOURCE = {Source.ing.name: IngParser()}


def parse_csv_files_as_df(csv_files: list[CsvFile]) -> pd.DataFrame:
    dfs = []
    for csv_file in csv_files:
        parser = PARSER_BY_SOURCE[csv_file.source.name]
        dfs.append(parser.parse(csv_file.path))

    df = pd.concat(dfs, ignore_index=True)
    df.drop_duplicates("transaction_id", inplace=True)
    return df


def parse_directory_as_df(root_input_files_dir) -> pd.DataFrame:
    """
    Example directories structure:
    <ROOT_INPUT_FILES_DIR>/ing/file_1.csv
    <ROOT_INPUT_FILES_DIR>/ing/file_2.csv
    <ROOT_INPUT_FILES_DIR>/mbank/file_1.csv
    """
    csv_files = []
    for source in list(Source):
        single_source_dir = os.path.join(root_input_files_dir, source.name)
        if not os.path.isdir(single_source_dir):
            log.warning(
                f"directory for source of type {source.name} not found (expected: {single_source_dir})"
            )
            continue

        file_names = os.listdir(single_source_dir)

        for file_name in file_names:
            file_path = os.path.join(single_source_dir, file_name)
            csv_files.append(CsvFile(file_path, source))

    if len(csv_files) == 0:
        msg = f"No input files discovered in {root_input_files_dir}"
        raise ValueError(msg)

    return parse_csv_files_as_df(csv_files)
