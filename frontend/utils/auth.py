import streamlit as st

def login_user():
    st.session_state['authenticated'] = True
    st.rerun()

def logout():
    st.session_state['authenticated'] = False
    st.rerun()