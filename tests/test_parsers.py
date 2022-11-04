import pytest
import os
from project.parsers import (
    IngParser,
    MbankParser,
    parse_csv_files_as_df,
    CsvFile,
    SourceType,
    parse_directory_as_df,
)


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "test_files")


def test_parse_csv_ing():
    input_file = os.path.join(
        TEST_DATA_DIR, "ing", "Lista_transakcji_example_ING_1.csv"
    )
    df = IngParser().parse(input_file)
    assert df.shape == (6, 8)


def test_parse_csv_mbank():
    input_file = os.path.join(
        TEST_DATA_DIR, "mbank", "Lista_transakcji_example_mbank_1.csv"
    )
    # input_file = (
    #     "C:/Users/pawel/git/money-insights/data/mbank/62929002_000804_221104.csv"
    # )
    df = MbankParser().parse(input_file)


def test_parse_csv_files_as_df():
    csv_files = [
        CsvFile(
            os.path.join(TEST_DATA_DIR, "ing", "Lista_transakcji_example_ING_1.csv"),
            SourceType.ing,
        ),
        CsvFile(
            os.path.join(TEST_DATA_DIR, "ing", "Lista_transakcji_example_ING_2.csv"),
            SourceType.ing,
        ),
    ]
    df = parse_csv_files_as_df(csv_files)
    assert df.shape == (12, 8)


def test_parse_directory_as_df():
    df = parse_directory_as_df(TEST_DATA_DIR)
    assert df.shape == (17, 8)
