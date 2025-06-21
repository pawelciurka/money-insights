from enum import StrEnum


class TransactionColumn(StrEnum):
    TRANSACTION_ID = 'transaction_id'
    TITLE = 'title'
    AMOUNT = 'amount'
    AMOUNT_ABS = 'amount_abs'
    CONTRACTOR = 'contractor'
    TRANSACTION_DATE = 'transaction_date'
    TRANSACTION_DATE_ISOSTR = 'transaction_date_isostr'
    TRANSACTION_DATE_ISOSTR_MONTH = 'transaction_date_isostr_month'
    TRANSACTION_DATE_ISOSTR_YEAR = 'transaction_date_isostr_year'

    CATEGORY = "category"
    CATEGORY_RULE_ID = "category_rule_id"

    ACCOUNT_NAME = 'account_name'
    SOURCE_FILE_PATH = "source_file_path"
    SOURCE_TYPE = "source_type"
    TYPE = "type"
    ONE_GROUP = "one_group"
    GROUP_VALUE = "group_value"

    DISPLAY_CATEGORY = "display_category"
    DISPLAY_TYPE = "display_type"

    # aggregated dataframes
    N_TRANSACTIONS = "n_transactions"
    MAX_DATE = "max_date"
    MIN_DATE = "min_date"
    DELTA = "delta"


class CategoryRuleColumn(StrEnum):
    RULE_ID = 'rule_id'
    COLUMN = 'column'
    RELATION = 'relation'
    VALUE = 'value'
    CATEGORY = 'category'


class TransactionType(StrEnum):
    INCOME = 'income'
    OUTCOME = 'outcome'
