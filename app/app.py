import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from src import compute_df, buy_price_ui, liquidity_selling_ui, format_time_plot


def main():
    # Render the readme as markdown using st.markdown.
    readme_text = st.markdown(get_file_content_as_a_string("app/instructions.md"))

    # Once we have the dependencies, add a selector for the app mode on the sidebar.
    st.sidebar.title("What to do")
    app_mode = st.sidebar.selectbox(
        "Choose the app mode",
        ["Run the app", "Show instructions", "Show the source code"],
    )
    if app_mode == "Show instructions":
        st.sidebar.success('To continue select "Run the app".')
    elif app_mode == "Show the source code":
        readme_text.empty()
        st.code(get_file_content_as_a_string("app/app.py"))
    elif app_mode == "Run the app":
        readme_text.empty()
        run_the_app()


def get_file_content_as_a_string(path):
    with open(path, "r") as file:
        return file.read()


def run_the_app():
    # To make Streamlit fast, st.cache allows us to reuse computation across runs.
    # In this common pattern, we download data from an endpoint only once.

    st.title("When will I be even?")

    # Get input parameters
    buying_price, mortgage_pct, mortgage_value, downpayment, fixed = buy_price_ui()

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

    # Hypotetical sell
    st.sidebar.header("My out")
    sale_value = st.sidebar.number_input(
        "Hypothetical sales price", 0, 1000000, buying_price
    )
    rent = st.sidebar.number_input("Saved from rent", 0.0, 10000.0, monthly_payment)

    # prepare dataframe
    df = compute_df(mortgage_value, duration_mnts, monthly_payment, interest_rate / 12, rent, sale_value)


    # figures
    ### Residual
    fig1 = go.Figure(layout={"title": "Residual Debt"})
    fig1.add_trace(
        go.Scatter(x=df["month"], y=df["cumulative payment"], name="Paid back")
    )
    fig1.add_trace(go.Scatter(x=df["month"], y=df["residual"], name="Residual"))
    fig1.add_hrect(y0=0.9, y1=2.6, line_width=0, fillcolor="red", opacity=0.2)

    fig1 = format_time_plot(fig1, duration_mnts)
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

    fig2 = format_time_plot(fig2, duration_mnts)
    st.plotly_chart(fig2, use_container_width=True)

    ### Total cost breakdown
    fig3 = go.Figure(
        go.Pie(
            labels=["Fixed", "Interests (full repayment)"],
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

    # Compute when you break even: when selling the house you get back your costs

    liquidity_selling_ui(df, downpayment, fixed)





if __name__ == "__main__":
    main()
