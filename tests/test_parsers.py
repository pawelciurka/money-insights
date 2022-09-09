import pytest
import os
from project.parsers import (
    IngParser,
    parse_csv_files_as_df,
    CsvFile,
    Source,
    parse_directory_as_df,
)


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "test_files")


def test_parse_csv_ing():
    input_file = os.path.join(
        TEST_DATA_DIR, "ing", "Lista_transakcji_example_ING_1.csv"
    )
    df = IngParser().parse(input_file)
    assert df.shape == (6, 7)


def test_parse_csv_files_as_df():
    csv_files = [
        CsvFile(
            os.path.join(TEST_DATA_DIR, "ing", "Lista_transakcji_example_ING_1.csv"),
            Source.ing,
        ),
        CsvFile(
            os.path.join(TEST_DATA_DIR, "ing", "Lista_transakcji_example_ING_2.csv"),
            Source.ing,
        ),
    ]
    df = parse_csv_files_as_df(csv_files)
    assert df.shape == (12, 7)


def test_parse_directory_as_df():
    df = parse_directory_as_df(TEST_DATA_DIR)
    assert df.shape == (12, 7)
