from dataclasses import dataclass
from datetime import date
import csv
from io import TextIOWrapper

import pandas as pd
import unicodedata
import codecs
from io import StringIO


@dataclass
class CsvCol:
    index: int
    name: str
    dtype: type


input_cols_ing: list[CsvCol] = [
    CsvCol(0, "transaction_date", date),
    CsvCol(2, "contrctor", str),
    CsvCol(3, "title", str),
    CsvCol(8, "amount", float),
    CsvCol(15, "account_name", str),
]


class Parser:
    def parse(self, file_path) -> pd.DataFrame:
        csv_str = self.input_to_string_io(file_path)

        # read as dataframe
        df = pd.read_csv(csv_str, **self.read_csv_kwargs)

        # translate
        df["transaction_date"] = df["transaction_date"].map(date.fromisoformat)
        df["amount"] = df["amount"].map(lambda x: float(x.replace(",", ".")))

        # add columns
        df["type"] = df["amount"].map(lambda x: "income" if x >= 0 else "outcome")
        return df


class IngParser(Parser):
    read_csv_kwargs = dict(
        sep=";",
        header=None,
        usecols=[ic.index for ic in input_cols_ing],
        names=[ic.name for ic in input_cols_ing],
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

    def input_to_string_io(self, file_path: str) -> StringIO:
        with codecs.open(file_path, "rb", "cp1250") as f:
            lines = f.readlines()
            lines_n = self.normalize_lines(lines)
            lines_nt = self.truncate_header(lines_n)
        string_io = StringIO(b"".join(lines_nt).decode("utf-8"))
        return string_io
