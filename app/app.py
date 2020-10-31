import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
import plotly.express as px
import numpy as np


st.title("When will I be even?")

buying_price = st.sidebar.number_input("Buying price", value = 250000, min_value=0, max_value=100000000000)
mortgage_pct = st.sidebar.number_input("Mortgage value (%)", value=80, min_value=0, max_value=100)
mortgage_value = buying_price/100*mortgage_pct
st.sidebar.text("Mortgage: {}".format(mortgage_value))
duration_yrs = st.sidebar.number_input("Mortgage duration (yrs)", value = 30, min_value=0, max_value=35)
duration_mnts = duration_yrs * 12
interest_rate = st.sidebar.number_input("Yearly interest rate (%)", value = 1.45, min_value=0., max_value=10.)

monthly_payment = np.pmt(interest_rate / 12 / 100, duration_mnts, -mortgage_value)
st.sidebar.text("Monthly payment: %.2f €" %monthly_payment)


months = np.arange(0, duration_mnts, 1)
payments = monthly_payment * np.ones(duration_mnts)
principal

df = pd.DataFrame({"months" : months, "monthly payment" : payments})
df.loc[:, 'cumulative payment'] = df.loc[:, "monthly payment"].cumsum()


fig = px.line(df, x="months", y=["cumulative payment", "monthly payment"], title='Life expectancy in Canada')

st.plotly_chart(fig, use_container_width=True)


df