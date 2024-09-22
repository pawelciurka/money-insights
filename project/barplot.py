import pandas as pd
import plotly.graph_objs as go


def get_barplot(
    df_income: pd.DataFrame,
    df_outcome: pd.DataFrame,
    view_income=True,
    view_expense=True,
):
    if int(view_expense) + int(view_income) == 1:
        expense_bar_offset = -0.2
        income_bar_offset = -0.2
    else:
        expense_bar_offset = 0.0
        income_bar_offset = -0.4

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
            font=dict(size=12),
            legend_orientation="h",
            hovermode="x",
            # margin=dict(b=0, t=10, l=0, r=10),
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
                width=0.4,
                legendgroup="outcome",
                legendgrouptitle_text="outcome",
                name=col,
            )

    # Add the traces
    if view_income:
        for col in df_income.columns:
            if (df_income[col] == 0).all():
                continue
            fig.add_bar(
                x=df_income.index,
                y=df_income[col],
                # Set the right yaxis depending on the selected product (from enumerate)
                yaxis=f"y2",
                # Offset the bar trace, offset needs to match the width
                # The values here are in milliseconds, 1billion ms is ~1/3 month
                offsetgroup="2",
                offset=income_bar_offset,
                width=0.4,
                legendgroup="income",
                legendgrouptitle_text="income",
                name=col,
            )

    return fig
