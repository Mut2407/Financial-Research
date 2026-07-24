import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


pytestmark = [pytest.mark.integration, pytest.mark.frontend]
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_streamlit_dataframe_reruns_are_stable_with_system_arrow_allocator():
    """Exercise Arrow IPC serialization in a child process.

    A native crash cannot be caught by pytest in-process. Running the Streamlit
    reruns in a child process makes SIGSEGV observable as a non-zero return code
    while keeping the rest of the test suite alive.
    """
    script = textwrap.dedent(
        '''
        import pyarrow as pa
        from streamlit.testing.v1 import AppTest

        assert pa.default_memory_pool().backend_name == "system"
        app_source = """\
        import pandas as pd
        import streamlit as st

        frame = pd.DataFrame({"ticker": ["FPT"] * 500, "close": range(500)})
        st.dataframe(frame, width="stretch", hide_index=True)
        """
        app = AppTest.from_string(app_source, default_timeout=15)
        for _ in range(30):
            app.run()
            assert not app.exception
        print("streamlit-arrow-reruns-ok")
        '''
    )
    environment = os.environ.copy()
    environment["ARROW_DEFAULT_MEMORY_POOL"] = "system"
    environment["PYTHONFAULTHANDLER"] = "1"

    result = subprocess.run(
        [sys.executable, "-X", "faulthandler", "-c", script],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, (
        "Streamlit/Arrow child process failed.\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert "streamlit-arrow-reruns-ok" in result.stdout
