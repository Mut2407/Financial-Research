import streamlit as st

def render():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>📝 Register</h2>", unsafe_allow_html=True)
        with st.container(border=True):
            st.text_input("Email")
            st.text_input("Password", type="password")
            st.button("Register & Login", width="stretch", type="primary")
            
            if st.button("Back to Login"):
                st.session_state.show_register = False
                st.rerun()
