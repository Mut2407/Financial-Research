import sys
from pathlib import Path

import pytest


FRONTEND_ROOT = Path(__file__).resolve().parents[2] / "frontend"
if str(FRONTEND_ROOT) not in sys.path:
    sys.path.insert(0, str(FRONTEND_ROOT))


@pytest.fixture(autouse=True)
def clear_streamlit_caches():
    import streamlit as st

    st.cache_data.clear()
    yield
    st.cache_data.clear()
