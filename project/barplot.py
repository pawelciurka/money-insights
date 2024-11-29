import pandas as pd
import plotly.graph_objs as go


def get_barplot(
    df_income: pd.DataFrame,
    df_outcome: pd.DataFrame,
    df_delta: pd.DataFrame,
    view_income=True,
    view_expense=True,
    view_delta=True,
):
    income_yaxis = 'y2'
    if int(view_expense) + int(view_income) + int(view_delta) == 1:
        expense_bar_offset = income_bar_offset = delta_bar_offset = -0.45
        expense_bar_width = income_bar_width = delta_bar_width = 0.9
    elif view_expense and view_income and view_delta:
        expense_bar_offset = -0.45
        income_bar_offset = -0.05
        delta_bar_offset = 0.35
        expense_bar_width = income_bar_width = 0.4
        delta_bar_width = 0.1
    elif view_income and view_delta:
        income_bar_offset = -0.4
        delta_bar_offset = 0.0
        income_bar_width = 0.4
        delta_bar_width = 0.1
        income_yaxis = None # misc bug, not obvious solution
    elif view_expense and (view_income or view_delta):
        expense_bar_offset = -0.4
        income_bar_offset = delta_bar_offset = 0.0
        expense_bar_width = income_bar_width = 0.4
        delta_bar_width = 0.1

    fig = go.Figure(
        layout=go.Layout(
            height=800,
            width=1000,
            barmode="relative",
            yaxis_showticklabels=True,
            yaxis_showgrid=True,
            # yaxis_range=[0, df.groupby(axis=1, level=0).sum().max().max() * 1.5],
            # Secondary y-axis overlayed on the primary one and not visible
            yaxis2=go.layout.YAxis(
                visible=True,
                matches="y",
                overlaying="y",
                anchor="x",
            ),
            yaxis3=go.layout.YAxis(
                visible=True,
                matches="y",
                overlaying="y",
                anchor="x",
            ),
            font=dict(size=12),
            legend_orientation="h",
            hovermode="x",
        )
    )

    if view_expense:
        for col in df_outcome.columns:
            if (df_outcome[col] == 0).all():
                continue
            fig.add_bar(
                x=df_outcome.index,
                y=df_outcome[col],
                # Set the right yaxis depending on the selected product (from enumerate)
                yaxis=f"y1",
                offsetgroup="1",
                offset=expense_bar_offset,
                width=expense_bar_width,
                legendgroup="outcome",
                legendgrouptitle_text="outcome",
                name=col,
            )

    if view_income:
        for col in df_income.columns:
            if (df_income[col] == 0).all():
                continue
            fig.add_bar(
                x=df_income.index,
                y=df_income[col],
                yaxis=income_yaxis,
                offsetgroup="2",
                offset=income_bar_offset,
                width=income_bar_width,
                legendgroup="income",
                legendgrouptitle_text="income",
                name=col,
            )

    if view_delta:
        colors = ['green' if v > 0.0 else 'red' for v in df_delta['delta']]

        fig.add_bar(
            x=df_delta.index,
            y=df_delta['delta'],
            # Set the right yaxis depending on the selected product (from enumerate)
            yaxis=f"y3",
            offsetgroup="3",
            offset=delta_bar_offset,
            width=delta_bar_width,
            legendgroup="delta",
            legendgrouptitle_text="delta",
            name='delta',
            marker={'color': colors},
        )

    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    return fig
