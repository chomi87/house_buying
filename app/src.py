import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


def compute_df(
    principal: float,
    duration: int,
    payment: float,
    ir_monthly: float,
    rent: float,
    sale_value: int,
):
    """
    Prepares dataframe given the parameters
    :param principal: mortgage value
    :param duration: in months
    :param payment: monthly repayment
    :param ir_monthly:
    :return: dataframe with the following columns ["month", "principal", "interest", "residual"] for the duration of the loan
    """
    result = []
    for month in range(1, duration + 1):
        interest = ir_monthly * principal / 100
        residual = principal + interest - payment

        row = {
            "month": month,
            "principal": principal,
            "interest": interest,
            "residual": residual,
        }
        result.append(row)

        principal = residual

    df = pd.DataFrame(result)
    df.loc[:, "monthly payment"] = payment
    df.loc[:, "cumulative payment"] = df.loc[:, "monthly payment"].cumsum()

    df.loc[:, "saved rent"] = df.loc[:, "month"] * rent
    df.loc[:, "Sales balance"] = sale_value - df.loc[:, "residual"]

    # include savings from non paid rent and cost from paid mortgage
    df.loc[:, "Rent mortgage cumdif"] = (
        -df.loc[:, "cumulative payment"] + df.loc[:, "saved rent"]
    )
    df.loc[:, "Sales balance incl monthly"] = (
        df["Sales balance"] + df.loc[:, "Rent mortgage cumdif"]
    )

    return df


def buy_price_ui():
    st.sidebar.markdown("### Purchase info")
    buy_price = st.sidebar.number_input(
        "Buying price", value=250000, min_value=0, max_value=100000000000
    )

    mortgage_pct = st.sidebar.number_input(
        "Mortgage value (%)", value=80, min_value=0, max_value=100
    )
    mortgage_value = buy_price / 100 * mortgage_pct

    st.sidebar.text("Mortgage: {}".format(mortgage_value))
    downpayment = buy_price - mortgage_value
    st.sidebar.text("Down payment: {}".format(downpayment))

    fixed = st.sidebar.number_input(
        "Fixed expenses (notary, taxes, ...) - estimate at 10% of the price",
        value=int(buy_price * 0.1),
        min_value=0,
        max_value=50000,
    )
    st.sidebar.text("Required liquidity: {}".format(downpayment + fixed))

    return buy_price, mortgage_pct, mortgage_value, downpayment, fixed


def liquidity_selling_ui(df, downpayment, fixed):
    st.markdown("### Liquidity when selling the house")
    include_savings = st.checkbox(
        "Include saving from rent and monthly mortgage repayement?"
    )

    def add_trace(fig, df, filter, col_x, col_y, label):
        fig.add_trace(
            go.Scatter(
                x=df[filter][col_x],
                y=df[filter][col_y],
                fill="tozeroy",
                name=label,
            )
        )
        return fig

    fig4 = go.Figure()
    if include_savings:
        at_loss_incl_monthly = df["Sales balance incl monthly"] < (downpayment + fixed)
        at_gain_incl_monhtly = df["Sales balance incl monthly"] > (downpayment + fixed)

        fig4 = add_trace(
            fig4,
            df,
            at_gain_incl_monhtly,
            "month",
            "Sales balance incl monthly",
            "At gain - incl rent and mortgage",
        )
        fig4 = add_trace(
            fig4,
            df,
            at_loss_incl_monthly,
            "month",
            "Sales balance incl monthly",
            "At loss - incl rent and mortgage",
        )

        break_even = df.loc[
            df["Sales balance incl monthly"].gt(downpayment + fixed).idxmax(), "month"
        ]

    else:
        at_loss = df["Sales balance"] < (downpayment + fixed)
        at_gain = df["Sales balance"] > (downpayment + fixed)
        fig4 = add_trace(
            fig4,
            df,
            at_gain,
            "month",
            "Sales balance",
            "At gain - excl rent and mortgage",
        )
        fig4 = add_trace(
            fig4,
            df,
            at_loss,
            "month",
            "Sales balance",
            "At loss - excl rent and mortgage",
        )

        break_even = df.loc[
            df["Sales balance"].gt(downpayment + fixed).idxmax(), "month"
        ]

    fig4.add_trace(
        go.Scatter(
            x=df.loc[:, "month"],
            y=np.ones(len(df)) * (downpayment + fixed),
            name="Costs + Downpayment",
        )
    )

    fig4 = format_time_plot(fig4, len(df))

    # Break even arrow annotation

    fig4.add_annotation(
        x=break_even,
        y=downpayment + fixed,
        text="Break even at month {}".format(break_even),
        showarrow=True,
        arrowhead=1,
        yshift=10,
    )

    st.plotly_chart(fig4, use_container_width=True)


def format_time_plot(fig, duration_mnts):

    x_ticks_values = list(range(0, duration_mnts + 1, 60))
    x_ticks_text = [x / 12 for x in x_ticks_values]

    fig.update_layout(
        xaxis=dict(tickmode="array", tickvals=x_ticks_values, ticktext=x_ticks_text),
        xaxis_title="Years",
        hovermode="x unified",
    )

    return fig
