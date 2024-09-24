import csv
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import logging
from project.utils import calculate_md5

log = logging.getLogger(__name__)


class Relation(Enum):
    equals = 1
    contains = 2


@dataclass
class Condition:
    column: str
    relation: Relation
    value: str

    def evaluate(self, other_value: str):
        def equals(other_value: str):
            return self.value == other_value

        def contains(other_value: str):
            return self.value in other_value

        evaluator = {"equals": equals, "contains": contains}[self.relation.name]
        return evaluator(str(other_value))


@dataclass
class CategoryRule:
    category: str
    contitions: list[Condition]


@dataclass
class CategoriesRules:
    items: list[CategoryRule]
    csv_md5: str


categories_definitions_cols = ["rule_id", "column", "relation", "value", "category"]


def create_empty_categories_rules(categories_rules_csv_path: str):
    exemplary_data = [
        {
            categories_definitions_cols[0]: 1,
            categories_definitions_cols[1]: "contractor",
            categories_definitions_cols[2]: "contains",
            categories_definitions_cols[3]: "ZABKA",
            categories_definitions_cols[4]: "groceries",
        }
    ]
    pd.DataFrame(exemplary_data, columns=categories_definitions_cols).to_csv(
        categories_rules_csv_path, quoting=csv.QUOTE_NONNUMERIC, index=False
    )


def read_categories_rules(categories_rules_csv_path: str) -> CategoriesRules:
    log.info(f"Reading categories rules from {categories_rules_csv_path}")
    df = pd.read_csv(categories_rules_csv_path, usecols=categories_definitions_cols)

    items = []
    categories_rules = CategoriesRules(
        items=items, csv_md5=calculate_md5(categories_rules_csv_path)
    )
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

        items.append(CategoryRule(category=category, contitions=rule_conditions))

    # fallback category - goes last if no previous conditions were met
    items.append(
        CategoryRule(
            category="unrecognized",
            contitions=[Condition("title", Relation.contains, "")],
        )
    )
    log.info(f"Read {len(items)} categories rules from {categories_rules_csv_path}")

    return categories_rules


class CategoriesCache(dict):
    CSV_COLS = ["transaction_id", "category", "rules_csv_md5"]

    def __init__(self, *, file_path) -> None:
        self.file_path = file_path
        self.rules_csv_md5 = None
        super().__init__()

    def read(self) -> None:
        try:
            log.info(f"Trying to read precomputed categories from {self.file_path}")
            df = pd.read_csv(self.file_path, usecols=self.CSV_COLS)
        except:
            log.info(f"Couldn't read precomputed categories from {self.file_path}")
            return
        for r in df.itertuples():
            self[r.__getattribute__(self.CSV_COLS[0])] = r.__getattribute__(
                self.CSV_COLS[1]
            )
        self.md5 = list(set(df[self.CSV_COLS[2]]))[0]
        logging.info(f"Read {len(df)} precomputed categories")

    def write(self, category_by_id: dict[str, str], rules_csv_md5: str) -> None:
        df = pd.DataFrame.from_dict(
            category_by_id, orient="index", columns=[self.CSV_COLS[1]]
        )
        df["rules_csv_md5"] = rules_csv_md5
        df.to_csv(self.file_path, index_label=self.CSV_COLS[0])

    @property
    def is_empty(self):
        return bool(len(self) == 0)

    def __hash__(self):
        return self.rules_csv_md5

    def __eq__(self, other):
        return self.rules_csv_md5 == self.rules_csv_md5
