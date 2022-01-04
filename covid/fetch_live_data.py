from datetime import tzinfo
import requests
import pandas as pd
import json
import pendulum
import re
from bs4 import BeautifulSoup
import os
import numpy as np


dat = {
    "NEW": {
        "CLASS": "DAILY-CASES",
        "COLS": ["date","new","cases","ind","net"],
        "COL" : "new",
    },
    "HOSP": {
        "CLASS": "DAILY-HOSPITALISED",
        "COLS": ["date","hosp","icu","vent"],
        "COL" : "hosp",
    },
    "ICU": {
        "CLASS": "DAILY-HOSPITALISED",
        "COLS": ["date","hosp","icu","vent"],
        "COL" : "icu",
    },
    "VENT": {
        "CLASS": "DAILY-HOSPITALISED",
        "COLS": ["date","hosp","icu","vent"],
        "COL" : "vent",
    },
    "TESTS": {
        "CLASS": "DAILY-TESTS",
        "COLS": ["date","tests","var","net"],
        "COL" : "net",
    },
}

def getresp(url):
    
    r = requests.get(url,verify=False)
    return r

def get_vic(dtstr):
    url = 'https://www.dhhs.vic.gov.au/ncov-covid-cases-by-lga-source-csv'
    r = getresp(url)
    rows=[]
    for cols in r.text.split("\r\n"):
        row = re.sub(r',(?=")','~', cols)
        rows.append(row.split(","))
    columns = rows.pop(0)
    df = pd.DataFrame(rows, columns=columns)
    df = df.loc[df.diagnosis_date.astype(str) != '']
    df["state"] = "VIC"
    df["diagnosis_date"] = pd.to_datetime(df["diagnosis_date"])
    df["confirmed_cases"] = 1
    df = df.loc[df.diagnosis_date >= dtstr].sort_values("diagnosis_date").reset_index().drop('index',axis=1)
    df = df.groupby(["diagnosis_date","state","Localgovernmentarea", "Postcode", "acquired"]).confirmed_cases.sum().reset_index() 
    df.rename(columns={"Localgovernmentarea": "lga", "Postcode": "postcode", "diagnosis_date" : "date" }, inplace=True)
    #df.groupby(["state","date"])["confirmed_cases"].sum().reset_index(), 
    return df 

def get_nsw(dtstr):
    
    url = 'https://data.nsw.gov.au/data/api/3/action/datastore_search_sql?sql=SELECT%20*%20from%20%2221304414-1ff1-4243-a5d2-f52778048b29%22%20WHERE%20notification_date>=%27{dtstr}%27'  
    r = getresp(url.format(dtstr=dtstr))
    res_json = r.json()
    df = pd.DataFrame(res_json["result"]["records"])
    df["state"] = "NSW"
    df["acquired"] = "Local"
    df["notification_date"] = pd.to_datetime(df["notification_date"])
    df["confirmed_cases"] = 1
    df = df.groupby(["notification_date","state","lga_name19", "postcode", "acquired"]).confirmed_cases.sum().reset_index()
    df.rename(columns={"lga_name19": "lga", "notification_date":"date"}, inplace=True)
    #df.groupby(["state","date"])["confirmed_cases"].sum().reset_index(), 
    return df 

def get_qld(dtstr):
    url = 'https://www.data.qld.gov.au/api/3/action/datastore_search_sql?sql=SELECT%20*%20from%20%221dbae506-d73c-4c19-b727-e8654b8be95a%22%20WHERE%20%22NOTIFICATION_DATE%22>=%27{dtstr}%27'  
    r = getresp(url.format(dtstr=dtstr))
    res_json = r.json()
    df = pd.DataFrame(res_json["result"]["records"])
    df["state"] = "QLD"
    df["NOTIFICATION_DATE"] = pd.to_datetime(df["NOTIFICATION_DATE"])
    df["confirmed_cases"] = 1
    df = df.groupby(["NOTIFICATION_DATE","state","LGA_NAME", "POSTCODE", "SOURCE_INFECTION"]).confirmed_cases.sum().reset_index()
    df.rename(columns={"LGA_NAME": "lga", "NOTIFICATION_DATE":"date", "SOURCE_INFECTION": "acquired" }, inplace=True)
    #df.groupby(["state","date"])["confirmed_cases"].sum().reset_index(), 
    return df 

def get_state(state, lookbackdays, key):
    url = 'https://covidlive.com.au/report/{mode}/{state}?sort=date'
    r = getresp(url.format(state=state.lower(), mode=dat[key]["CLASS"].lower()))
    soup = BeautifulSoup(r.content, 'html.parser')
    tbl = soup.find("table", {"class": dat[key]["CLASS"]})
    rows=[]
    for row in tbl.find_all("tr"):
        cols=[]
        data = row.find_all("td")
        for col in data:
            cols.append(col.get_text())
        rows.append(cols)
    df = pd.DataFrame(rows,columns=dat[key]["COLS"])
    df = df.loc[df.date.notna()]
    df[key.lower()] = df[dat[key]['COL']].replace("-",0).replace("",0)
    df.date = pd.to_datetime(df.date)
    df["state"] = state
    df = df.groupby(["state","date"])[key.lower()].sum().reset_index().rename(columns={key.lower():"confirmed_cases"}).sort_values("date")
    return df.iloc[lookbackdays*-1:]

def get_live_data(lookbackdays,fetch_threshold, key):
    proj_path = os.path.abspath(os.path.join(os.path.dirname(__file__))).replace("\\","/")
    fetchlive = False
    dfnat = None
    dfstate = None
    try:
        dfnat = pd.read_csv(proj_path +"/dfnat_{}.csv".format(key))
        dfnat.date = pd.to_datetime(dfnat.date)
        dfstate = pd.read_csv(proj_path +"/dfstate_{}.csv".format(key))
        dfstate.date = pd.to_datetime(dfstate.date)
    except:
        fetchlive = True


    if dfnat is not None:
        if pendulum.today().utcnow().diff(pendulum.datetime(dfnat.date.max().year,dfnat.date.max().month,dfnat.date.max().day )).days > fetch_threshold:
            fetchlive = True
    print(fetchlive)
    if fetchlive:    
        #dfnsw, dfnsw_lga_postcode = get_nsw(pendulum.today().subtract(days=lookbackdays).format("YYYY-MM-DD"))
        #dfvic, dfvic_lga_postcode = get_vic(pendulum.today().subtract(days=lookbackdays).format("YYYY-MM-DD"))
        #dfqld, dfqld_lga_postcode = get_qld(pendulum.today().subtract(days=lookbackdays).format("YYYY-MM-DD"))
        dfnsw = get_state("NSW",lookbackdays, key) 
        dfvic = get_state("VIC",lookbackdays, key) 
        dfqld = get_state("QLD",lookbackdays, key) 
        dfwa = get_state("WA",lookbackdays, key)
        dfsa = get_state("SA",lookbackdays, key)
        dfnt = get_state("NT",lookbackdays, key)
        dftas = get_state("TAS",lookbackdays, key)
        dfstate = pd.concat([dfnsw,dfvic, dfqld, dfwa, dfsa, dfnt, dftas])
        dfstate.confirmed_cases = dfstate.confirmed_cases.replace(np.nan,0)
        dfstate.confirmed_cases = dfstate.confirmed_cases.apply(lambda x: str(x).replace(',',''))
        dfstate.confirmed_cases = dfstate.confirmed_cases.astype(int)
        dfstate = dfstate.loc[dfstate.date <= pendulum.today().subtract(days=0).format("YYYY-MM-DD")]
        dfnat = dfstate.groupby("date")["confirmed_cases"].sum().reset_index()
        dfnat.to_csv(proj_path+"/dfnat_{}.csv".format(key), index=False)
        dfstate.to_csv(proj_path+"/dfstate_{}.csv".format(key), index=False)
    return dfnat, dfstate



