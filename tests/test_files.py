import pytest
import os
from project.parsers import IngParser


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "test_files")


def test_parse_csv_ing():
    input_file = os.path.join(TEST_DATA_DIR, "Lista_transakcji_example_ING.csv")
    IngParser().parse(input_file)
