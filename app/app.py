import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


def compute_df(principal: float, duration: int, payment: float, ir_monthly: float):
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

    return df

st.title("When will I be even?")

# Get input parameters
st.sidebar.header("I'm buying!")

buying_price = st.sidebar.number_input(
    "Buying price", value=250000, min_value=0, max_value=100000000000
)
mortgage_pct = st.sidebar.number_input(
    "Mortgage value (%)", value=80, min_value=0, max_value=100
)
mortgage_value = buying_price / 100 * mortgage_pct
st.sidebar.text("Mortgage: {}".format(mortgage_value))
downpayment = buying_price - mortgage_value
st.sidebar.text("Down payment: {}".format(downpayment))

fixed = st.sidebar.number_input(
    "Fixed expenses (notary, taxes, ...) - estimate at 10% of the price",
    value=int(buying_price * 0.1),
    min_value=0,
    max_value=50000,
)
st.sidebar.text("Required liquidity: {}".format(downpayment + fixed))

duration_yrs = st.sidebar.number_input(
    "Mortgage duration (yrs)", value=30, min_value=0, max_value=35
)
duration_mnts = duration_yrs * 12
interest_rate = st.sidebar.number_input(
    "Yearly interest rate (%)", value=1.45, min_value=0.0, max_value=10.0
)

monthly_payment = np.pmt(interest_rate / 12 / 100, duration_mnts, -mortgage_value)
total_payment = monthly_payment * duration_mnts
total_interest = np.round(total_payment - mortgage_value, 0)

st.sidebar.text("Monthly payment: %.2f €" % monthly_payment)


months = np.arange(1, duration_mnts + 1, 1)
payments = monthly_payment * np.ones(duration_mnts)

# Hypotetical sell
st.sidebar.header("My out")
sale_value = st.sidebar.number_input(
    "Hypothetical sales price", 0, 1000000, buying_price
)
rent = st.sidebar.number_input("Saved from rent", 0.0, 10000.0, monthly_payment)

# prepare dataframe
df = compute_df(mortgage_value, duration_mnts, monthly_payment, interest_rate / 12)
df.loc[:, "saved rent"] = df.loc[:, "month"] * rent
df.loc[:, "Sales balance"] = (
    sale_value
    - df.loc[:, "residual"]
)

# figures
### Residual
fig1 = go.Figure(layout={"title": "Residual Debt"})
fig1.add_trace(go.Scatter(x=df["month"], y=df["cumulative payment"], name="Paid back"))
fig1.add_trace(go.Scatter(x=df["month"], y=df["residual"], name="Residual"))
fig1.add_hrect(y0=0.9, y1=2.6, line_width=0, fillcolor="red", opacity=0.2)

x_ticks_values = list(range(0, duration_mnts+1, 60))
x_ticks_text= [x / 12 for x in x_ticks_values]

fig1.update_layout(
    xaxis = dict(
        tickmode = 'array',
        tickvals = x_ticks_values,
        ticktext = x_ticks_text
    ),
    xaxis_title="Years",
    hovermode="x unified"
)
st.plotly_chart(fig1, use_container_width=True)

### Monthly payment
fig2 = go.Figure(layout={"title": "Monthly Payment: %.2f €" % monthly_payment})
fig2.add_trace(
    go.Scatter(x=df["month"], y=df["interest"], fill="tozeroy", name="Interest")
)
fig2.add_trace(
    go.Scatter(
        x=df["month"], y=df["monthly payment"], fill="tonexty", name="On principal"
    )
)

fig2.update_layout(
    xaxis = dict(
        tickmode = 'array',
        tickvals = x_ticks_values,
        ticktext = x_ticks_text
    ),
    xaxis_title="Years"
)
st.plotly_chart(fig2, use_container_width=True)

### Total cost breakdown
fig3 = go.Figure(
    go.Pie(
        labels=["Fixed", "Interests"],
        values=[fixed, total_interest],
        insidetextorientation="radial",
    ),
    layout={"title": "Non recoverable costs %.0f €" % (fixed + total_interest)},
)
fig3.update_traces(
    hoverinfo="label+percent",
    textinfo="label+value",
    textfont_size=20,
    marker=dict(line=dict(color="#000000", width=2)),
)

st.plotly_chart(fig3, use_container_width=True)

### Situation at out

#Compute when you break even: when selling the house you get back your costs
break_even = df.loc[df["Sales balance"].gt(downpayment + fixed).idxmax(), "month"]
at_loss = df["Sales balance"] < (downpayment + fixed)
at_gain = df["Sales balance"] > (downpayment + fixed)

#include savings from non paid rent and cost from paid mortgage
df.loc[:, "Rent mortgage cumdif"] = - df.loc[:,"cumulative payment"] + df.loc[:, "saved rent"]
df.loc[:, "Sales balance incl monthly"] = df["Sales balance"] + df.loc[:, "Rent mortgage cumdif"]
at_loss_incl_monthly = df["Sales balance incl monthly"] < (downpayment + fixed)
at_gain_incl_monhtly = df["Sales balance incl monthly"] > (downpayment + fixed)

fig4 = go.Figure(
    layout={"title": "Liquidity when selling the house"},
)
fig4.add_trace(
    go.Scatter(x=df[at_gain]["month"], y=df[at_gain]["Sales balance"], fill="tozeroy", name="At gain")
)
fig4.add_trace(
    go.Scatter(x=df[at_loss]["month"], y=df[at_loss]["Sales balance"], fill="tozeroy", name="At loss")
)
fig4.add_trace(
    go.Scatter(x=df.loc[:,"month"], y=np.ones(len(df))*(downpayment+fixed), name="Costs + Downpayment")
)


fig4.add_trace(
    go.Scatter(x=df.loc[:,"month"], y=df["Sales balance incl monthly"], name="Incl rent and repayment")
)

fig4.update_layout(
    xaxis = dict(
        tickmode = 'array',
        tickvals = x_ticks_values,
        ticktext = x_ticks_text
    ),
    xaxis_title="Years"
)

fig4.add_annotation(x=break_even, y=downpayment + fixed,
            text="Break even at month {}".format(break_even),
            showarrow=True,
            arrowhead=1,
            yshift=10)


st.plotly_chart(fig4, use_container_width=True)