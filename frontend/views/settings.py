import streamlit as st

from utils.api_client import API_BASE_URL, ApiClientError, get_health


def render() -> None:
    st.markdown("### System Settings")
    st.code(f"API_BASE_URL={API_BASE_URL}")
    if st.button("Kiểm tra kết nối backend", type="primary"):
        try:
            health = get_health()
            st.success("Backend đang hoạt động.")
            st.json(health)
        except ApiClientError as error:
            st.error(str(error))

    st.info("API key và secrets chỉ được cấu hình trong `.env`; frontend không hiển thị hoặc lưu các giá trị này.")
