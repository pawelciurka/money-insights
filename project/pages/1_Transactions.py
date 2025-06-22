from typing import Optional
import streamlit as st
import streamlit_antd_components as sac


from project.categories import add_category_rule
from project.constants import UNRECOGNIZED
from project.dates_utils import get_past_month_start_datetime
from project.transactions_tree import get_sac_tree_items
from project.utils import get_emoji


from datetime import datetime, timedelta
import logging
import pandas as pd
from project.settings import CATEGORIES_RULES_FILE_PATH
from project.dates_utils import NOW
from project.transactions_state import get_state_transactions_df
from project.transactions_aggregation import (
    FREQUENCIES,
    get_time_aggregated_summarized_delta_df,
    get_time_aggregated_transactions_df,
)
from project.transactions_read import TransactionColumn
from project.barplot import get_barplot
from project.app_data import read_fresh_data

log = logging.getLogger(__name__)
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

all_categories, all_transactions_df = read_fresh_data()


@st.dialog("Create categories rule")
def create_category_rule(transaction_row: pd.Series):

    column = st.selectbox(
        "Column",
        options=[
            TransactionColumn.CONTRACTOR,
            TransactionColumn.TITLE,
            TransactionColumn.TRANSACTION_ID,
            TransactionColumn.DESCRIPTION,
        ],
        index=0,
    )
    relation = st.selectbox("Relation", options=['equals', 'contains'])
    value = st.text_area(
        "Value",
        value=transaction_row[column] if column is not None else "",
        disabled=column is None,
    )
    category = st.selectbox(
        "Category",
        options=all_categories,
        index=None,
        format_func=lambda c: f"{get_emoji(c)}{c}",
    )

    can_submit = column and relation and value and category

    if st.button("Add to categories rule", disabled=not can_submit):
        add_category_rule(
            CATEGORIES_RULES_FILE_PATH,
            column=column,
            relation=relation,
            value=value,
            category=category,
        )
        st.rerun()


expenses_container = st.container()

with expenses_container:
    (
        frequency_container,
        group_by_container,
        start_date_container,
        end_date_container,
    ) = st.columns(4)
    with frequency_container:
        frequency = st.selectbox(
            "Frequency",
            [f for f in FREQUENCIES],
            format_func=lambda x: x.display_name,
            index=1,
        )
    with group_by_container:
        group_by_col = st.selectbox(
            "Group by",
            ("one_group", "contractor", "account_name", "category"),
            index=3,
            format_func=lambda x: {"one_group": "None"}.get(x, x),
        )
    with start_date_container:
        start_year = NOW.year if NOW.month > 1 else NOW.year - 1
        start_date = st.date_input(
            "Start Date", value=get_past_month_start_datetime(n_months_back=1)
        )
        start_date = datetime.combine(start_date, datetime.min.time())
    with end_date_container:
        end_date = st.date_input("End Date")
        end_date = datetime.combine(end_date, datetime.min.time()) + timedelta(
            hours=23, minutes=59, seconds=59
        )

    pills_container = st.container()

    with pills_container:
        categories_pills_labels = {0: 'all categories', 1: f'{UNRECOGNIZED} only'}
        categories_lists = {
            0: [c for c in all_categories if c != "own-transfer"],
            1: [UNRECOGNIZED],
        }
        selected_category_pill_index = st.pills(
            label='categories pills',
            options=categories_pills_labels.keys(),
            format_func=lambda i: categories_pills_labels[i],
            label_visibility='collapsed',
            default=0,
        )

    categories_container = st.container()
    multiselect_kwargs = {
        'label': "Categories",
        'options': all_categories,
        'format_func': lambda c: f"{get_emoji(c)}{c}",
        'label_visibility': 'collapsed',
    }
    if selected_category_pill_index is not None:
        multiselect_kwargs['default'] = categories_lists[selected_category_pill_index]
        categories = categories_container.multiselect(**multiselect_kwargs)
    else:
        categories = categories_container.multiselect(**multiselect_kwargs)

    transactions_table_tab, barplot_tab, transactions_tree_tab = st.tabs(
        ["Transactions List", "Stacked Bar", "Transactions Tree"],
    )

    with barplot_tab:
        income_toggle_container, expense_toggle_container, delta_toggle_container, _ = (
            st.columns([0.25, 0.25, 0.25, 0.25])
        )
        with income_toggle_container:
            view_income = st.toggle("Show income", value=False)
        with expense_toggle_container:
            view_expense = st.toggle("Show expense", value=True)
        with delta_toggle_container:
            view_delta = st.toggle("Show delta", value=True)
        barplot_container = st.container()
        n_groups_container = st.container()
        table_container = st.container()

    with transactions_table_tab:
        (
            order_by_col_container,
            columns_toggle_container,
            _,
            transactions_number_container,
        ) = st.columns([0.25, 0.25, 0.25, 0.25])
        with columns_toggle_container:
            show_all_columns = st.toggle("Show all columns", value=False)
        with order_by_col_container:
            order_by_command = st.selectbox(
                label="Order by",
                options=[
                    "transaction_date:ascending",
                    "transaction_date:descending",
                    "amount_abs:descending",
                ],
                label_visibility="collapsed",
            )

    with transactions_tree_tab:
        open_all = st.checkbox(label='open all', value=False)
        swap_tree = st.checkbox(label='swap', value=False)
        tree_container = st.container()

    with n_groups_container:
        n_biggest_groups = st.slider(
            "Number of groups", min_value=1, max_value=50, value=7, step=1
        )

    state_transactions_df = get_state_transactions_df(
        all_transactions_df=all_transactions_df,
        categories=categories,
        start_date=start_date,
        end_date=end_date,
        group_by_col=group_by_col,
        n_biggest_groups=n_biggest_groups,
        order_by_command=order_by_command,
    )

    _df_income = get_time_aggregated_transactions_df(
        state_transactions_df[state_transactions_df["type"] == "income"],
        frequency=frequency,
    )
    _df_expense = get_time_aggregated_transactions_df(
        state_transactions_df[state_transactions_df["type"] == "outcome"],
        frequency=frequency,
    )

    _df_delta = get_time_aggregated_summarized_delta_df(_df_income, _df_expense)

    if len(state_transactions_df) == 0:
        st.toast('All transactions were excluded! Change filters ;)', icon="🚨")

    with barplot_container:
        st.plotly_chart(
            get_barplot(
                _df_income,
                _df_expense,
                _df_delta,
                view_income=view_income,
                view_expense=view_expense,
                view_delta=view_delta,
            ),
            use_container_width=True,
            config={'displayModeBar': False},
        )

    with table_container:
        st.dataframe(
            _df_expense.transpose(),
            use_container_width=True,
        )

    # table
    with transactions_table_tab:
        with transactions_number_container:
            st.text(f"{len(state_transactions_df)} transactions")
        if len(state_transactions_df) > 0:
            dataframe_state = st.dataframe(
                state_transactions_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="transaction_id",
                column_order=(
                    [
                        "transaction_date",
                        "display_type",
                        "display_category",
                        "contractor",
                        "title",
                        "amount_abs",
                    ]
                    if not show_all_columns
                    else None
                ),
                column_config={
                    "transaction_date": st.column_config.DateColumn(
                        label="transaction_date", width="small"
                    ),
                    "display_type": st.column_config.TextColumn(
                        label="type", width="small"
                    ),
                    "display_category": st.column_config.TextColumn(
                        label="category", width="small"
                    ),
                    'amount_abs': st.column_config.ProgressColumn(
                        label='amount',
                        width="small",
                        help=None,
                        format="%.2f",
                        min_value=0,
                        max_value=state_transactions_df['amount_abs'].quantile(0.90),
                    ),
                },
            )
            selected_row_index: Optional[int] = (
                dataframe_state['selection']['rows'][0]
                if dataframe_state['selection']['rows']
                else None
            )
            row_selected = selected_row_index is not None
            unrecognized_category_selected = (
                False
                if not row_selected
                else state_transactions_df.iloc[selected_row_index]["category"]
                == UNRECOGNIZED
            )
            st.button(
                "Create category rule",
                on_click=create_category_rule,
                args=(
                    (
                        state_transactions_df.iloc[selected_row_index]
                        if selected_row_index is not None
                        else None
                    ),
                ),
                disabled=not unrecognized_category_selected,
                help="Select an unrecognized transaction to create a rule based on it",
            )

    with tree_container:
        nesting_cols = []
        if group_by_col is not None:
            nesting_cols.append(group_by_col)

        if frequency.tree_supported:
            nesting_cols.append(
                {
                    'Month': "transaction_date_isostr_month",
                    "Year": 'transaction_date_isostr_year',
                    "Day": 'transaction_date_isostr',
                }.get(frequency.display_name)
            )

        if not nesting_cols:
            st.warning('Unsupported group by and frequency combination')

        if swap_tree:
            nesting_cols.reverse()

        items = get_sac_tree_items(
            transactions_df=state_transactions_df, nesting_cols=nesting_cols
        )

        sac.tree(
            items,
            width=1000,
            size='lg',
            open_index=0,
            open_all=open_all,
        )
