import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from covid.fetch_live_data import *
title = {
    "NEW": "New Cases",
    "HOSP": "Hospitalization",
    "ICU": "ICU Cases",
    "VENT": "Ventilation",
    "TESTS": "Testing"
}
def do_covid(o, key):
    o.title("Covid 19")
    o.subheader(title[key])
    #if o.button("Get Data"):
    dfnat, dfstate = get_live_data(90, -1, key)
    state_option = o.selectbox("Choose State or National", ('National','NSW','VIC','QLD','WA','SA','TAS','NT'), index=1)
    df = dfnat
    if state_option != 'National':
        df = dfstate.loc[dfstate.state==state_option]

    
    #recent_cases = 
    col1, col2, col3, col4, col5 = o.columns(5)
    cols = [col1, col2, col3, col4, col5]
    for i in range (-5,0):
        col = cols[5+i]
        case1 = int(df.iloc[i:].confirmed_cases.values[0])
        case2 = int(df.iloc[i - 1:].confirmed_cases.values[0])
        strdate = df.iloc[i:].date.dt.strftime('%d %b, %Y').head(1).values[0]
        col.metric(strdate, case1, case1-case2)
        #st.write(strdate)
    o.line_chart(df[["date","confirmed_cases"]].set_index("date"))

