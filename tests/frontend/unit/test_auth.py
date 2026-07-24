import pytest

from utils import auth


pytestmark = [pytest.mark.unit, pytest.mark.frontend]


class FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        self.rerun_count = 0

    def rerun(self):
        self.rerun_count += 1


def test_login_sets_authenticated_state_and_reruns(monkeypatch):
    fake_streamlit = FakeStreamlit()
    monkeypatch.setattr(auth, "st", fake_streamlit)

    auth.login_user()

    assert fake_streamlit.session_state["authenticated"] is True
    assert fake_streamlit.rerun_count == 1


def test_logout_clears_authenticated_state_and_reruns(monkeypatch):
    fake_streamlit = FakeStreamlit()
    fake_streamlit.session_state["authenticated"] = True
    monkeypatch.setattr(auth, "st", fake_streamlit)

    auth.logout()

    assert fake_streamlit.session_state["authenticated"] is False
    assert fake_streamlit.rerun_count == 1
