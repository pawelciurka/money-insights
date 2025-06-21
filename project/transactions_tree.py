import pandas as pd
import streamlit_antd_components as sac

from project.enums import TransactionColumn, TransactionType


def _prepare_items_tree(transactions_df: pd.DataFrame, nesting_cols: list[str]):
    items_lookup = {}
    items = []

    for group_labels, _ in transactions_df.groupby(nesting_cols):
        for i_level, group_label in enumerate(group_labels):
            path = tuple(group_labels[: i_level + 1])
            if path not in items_lookup:
                item = sac.TreeItem(group_label)
                if i_level == 0:
                    item.children = []
                    items.append(item)
                    items_lookup[path] = item
                else:
                    parent_path = tuple(group_labels[:i_level])
                    items_lookup[parent_path].children.append(item)
                    items_lookup[path] = item

    return items, items_lookup


def get_sac_tree_items(transactions_df: pd.DataFrame, nesting_cols: list[str]):
    transactions_df = transactions_df.copy()
    transactions_df.sort_values(nesting_cols, inplace=True)

    items, items_lookup = _prepare_items_tree(
        transactions_df=transactions_df, nesting_cols=nesting_cols
    )

    for path in items_lookup.keys():
        mask = pd.Series(True, index=transactions_df.index)
        for column, value in zip(nesting_cols, path):
            mask = mask & (transactions_df[column] == value)

        total_amount = sum(transactions_df[mask][TransactionColumn.AMOUNT])
        n_transactions = sum(mask)
        items_lookup[path].tag = [
            sac.Tag(n_transactions),
            sac.Tag(
                f"total: {total_amount:,.2f} zł",
                color='green' if total_amount > 0 else 'yellow',
            ),
        ]

    for group_values, group_transactions_df in transactions_df.groupby(nesting_cols):
        items_lookup[tuple(group_values)].children = [
            sac.TreeItem(
                " | ".join(
                    [
                        t.__getattribute__(TransactionColumn.TRANSACTION_DATE_ISOSTR),
                        t.__getattribute__(TransactionColumn.TITLE),
                        t.__getattribute__(TransactionColumn.CONTRACTOR),
                    ]
                ),
                tag=sac.Tag(
                    f"{t.amount_abs:,.2f} zł",
                    color={
                        TransactionType.INCOME: 'green',
                        TransactionType.OUTCOME: 'yellow',
                    }[t.type],
                ),
            )
            for t in group_transactions_df.itertuples()
        ]

    return items
