import streamlit as st
from bs4 import BeautifulSoup
from covid.covid import *



apps = {    
    'New Cases' : 'do_covid(o,"NEW")', 
    'Hospitalised' : 'do_covid(o,"HOSP")', 
    'Tests' : 'do_covid(o,"TESTS")', 
    'ICU' : 'do_covid(o,"ICU")', 
}

def init():
    if 'app' not in st.session_state:
        app = "New Cases"
        st.session_state['app'] = app

    else:
        app = st.session_state['app']
    
    st.set_page_config(
        page_title="My Toolbox",
        page_icon=":shark",
        layout = "wide"
    )

    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True) 




def run_app(app, o):
    _run_ = apps[app]
    eval(_run_)


def main():
    init()
    #st.sidebar.subheader("Apps")

    for key in apps:
        if st.sidebar.button(key):
            st.session_state['app'] = key

    exp1 =  st.container()
    run_app(st.session_state['app'], exp1)

if __name__ == "__main__":
    main()