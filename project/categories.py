import csv
from dataclasses import dataclass
from enum import Enum

import pandas as pd
import logging
from project.utils import calculate_md5
from project.enums import CategoryRuleColumn, TransactionColumn

log = logging.getLogger(__name__)


class Relation(Enum):
    equals = 1
    contains = 2
    is_lower_than = 3


@dataclass
class Condition:
    column: str
    relation: Relation
    value: str

    def evaluate(self, other_value: str) -> bool:
        def equals() -> bool:
            return self.value == str(other_value)

        def contains() -> bool:
            return self.value in other_value

        def is_lower_than() -> bool:
            return self.value >= other_value

        return {
            "equals": equals,
            "contains": contains,
            "is_lower_than": is_lower_than,
        }[self.relation.name]()


@dataclass
class CategoryRule:
    rule_id: int | None
    category: str
    conditions: list[Condition]


@dataclass
class CategoriesRules:
    items: list[CategoryRule]
    csv_md5: str

    @property
    def df(self) -> pd.DataFrame:
        d = []
        for rule in self.items:
            for condition in rule.conditions:
                d.append(
                    {
                        CategoryRuleColumn.RULE_ID: rule.rule_id,
                        CategoryRuleColumn.COLUMN: condition.column,
                        CategoryRuleColumn.RELATION: condition.relation.name,
                        CategoryRuleColumn.VALUE: condition.value,
                        CategoryRuleColumn.CATEGORY: rule.category,
                    }
                )
        return pd.DataFrame(d)

    @property
    def max_rule_id(self) -> int:
        return int(max([item.rule_id for item in self.items]))


def read_categories_rules(
    categories_rules_csv_path: str, add_fallback: bool = True
) -> CategoriesRules:
    categories_definitions_cols = [
        CategoryRuleColumn.RULE_ID,
        CategoryRuleColumn.COLUMN,
        CategoryRuleColumn.RELATION,
        CategoryRuleColumn.VALUE,
        CategoryRuleColumn.CATEGORY,
    ]
    log.info(f"Reading categories rules from {categories_rules_csv_path}")
    df = pd.read_csv(categories_rules_csv_path, usecols=categories_definitions_cols)

    items = []
    categories_rules = CategoriesRules(
        items=items, csv_md5=calculate_md5(categories_rules_csv_path)
    )
    for rule_id, rule_conditions_df in df.groupby(CategoryRuleColumn.RULE_ID):
        if len(set(rule_conditions_df[CategoryRuleColumn.CATEGORY])) != 1:
            raise AssertionError(
                f"Categories for rule {rule_id} differ between conditions!"
            )

        category = rule_conditions_df[CategoryRuleColumn.CATEGORY].iloc[0]
        rule_conditions = []
        for _, condition in rule_conditions_df.iterrows():
            rule_conditions.append(
                Condition(
                    column=condition[CategoryRuleColumn.COLUMN],
                    relation=Relation[condition[CategoryRuleColumn.RELATION]],
                    value=condition[CategoryRuleColumn.VALUE],
                )
            )

        items.append(
            CategoryRule(
                rule_id=int(rule_id), category=category, conditions=rule_conditions
            )
        )

    if add_fallback:
        # fallback category - goes last if no previous conditions were met
        items.append(
            CategoryRule(
                rule_id=None,
                category="unrecognized",
                conditions=[Condition("title", Relation.contains, "")],
            )
        )
    log.info(f"Read {len(items)} categories rules from {categories_rules_csv_path}")

    return categories_rules


def add_category_rule(
    categories_rules_csv_path: str,
    column: str,
    relation: str,
    value: str,
    category: str,
):
    categories_rules = read_categories_rules(
        categories_rules_csv_path=categories_rules_csv_path, add_fallback=False
    )

    categories_rules.items.append(
        CategoryRule(
            rule_id=categories_rules.max_rule_id + 1,
            category=category,
            conditions=[
                Condition(column=column, relation=Relation[relation], value=value)
            ],
        )
    )
    save_categories_rules_as_csv(
        categories_rules_csv_path=categories_rules_csv_path,
        categories_rules=categories_rules,
    )


def save_categories_rules_as_csv(
    categories_rules_csv_path: str, categories_rules: CategoriesRules
):
    categories_rules.df.to_csv(
        categories_rules_csv_path, index=False, quoting=csv.QUOTE_NONNUMERIC
    )


class CategoriesCache(dict):
    _mandatory_csv_cols = [
        TransactionColumn.TRANSACTION_ID,
        TransactionColumn.CATEGORY,
        TransactionColumn.CATEGORY_RULE_ID,
    ]

    def __init__(self, *, file_path) -> None:
        self.file_path = file_path
        super().__init__()

    def read(self) -> None:
        try:
            log.info(f"Trying to read categories cache from {self.file_path}")
            df = pd.read_csv(self.file_path, usecols=self._mandatory_csv_cols)
        except:
            log.info(f"Couldn't read categories cache from {self.file_path}")
            return
        for r in df.itertuples():
            self[r.__getattribute__(TransactionColumn.TRANSACTION_ID)] = (
                r.__getattribute__(TransactionColumn.CATEGORY),
                r.__getattribute__(TransactionColumn.CATEGORY_RULE_ID),
            )
        logging.info(f"Read categories for {len(df)} transactions")

    def write(self, transactions_df: pd.DataFrame) -> None:
        df = transactions_df[self._mandatory_csv_cols].copy()
        df.to_csv(self.file_path, index=False)

    @property
    def is_empty(self):
        return bool(len(self) == 0)

    def __hash__(self):
        # remove?
        return self.rules_csv_md5
