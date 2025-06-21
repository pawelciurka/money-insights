from enum import StrEnum


class TransactionColumn(StrEnum):
    TRANSACTION_DATE = 'transaction_date'
    CONTRACTOR = 'contractor'
    TITLE = 'title'
    TRANSACTION_ID = 'transaction_id'
    AMOUNT = 'amount'
    ACCOUNT_NAME = 'account_name'
    SOURCE_FILE_PATH = "source_file_path"
    SOURCE_TYPE = "source_type"
