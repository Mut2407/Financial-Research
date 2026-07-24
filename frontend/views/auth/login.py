import streamlit as st
from utils.auth import login_user

def render():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>🔐 Login to FSD Terminal</h2>", unsafe_allow_html=True)
        with st.container(border=True):
            st.text_input("Username")
            st.text_input("Password", type="password")
            if st.button("Sign In", width="stretch", type="primary"):
                login_user()
            
            if st.button("Create an account"):
                st.session_state.show_register = True
                st.rerun()
