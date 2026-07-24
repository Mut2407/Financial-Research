import pytest

from src.settings import Settings


pytestmark = pytest.mark.unit


def test_provider_api_key_is_masked_in_settings_representation(settings_factory):
    secret = "provider-secret-must-not-leak"
    config = settings_factory(data_provider_api_key=secret)

    assert config.data_provider_api_key.get_secret_value() == secret
    assert secret not in repr(config)
    assert "**********" in repr(config)


def test_vnstock_api_key_is_separate_and_masked(settings_factory):
    secret = "vnstock-secret-must-not-leak"
    config = settings_factory(vnstock_api_key=secret)

    assert config.vnstock_api_key.get_secret_value() == secret
    assert secret not in repr(config)


def test_vnstock_api_key_loads_from_official_environment_name(monkeypatch):
    secret = "official-vnstock-env-key"
    monkeypatch.setenv("VNSTOCK_API_KEY", secret)

    config = Settings(_env_file=None)

    assert config.vnstock_api_key.get_secret_value() == secret
    assert secret not in repr(config)


def test_provider_api_key_defaults_to_empty_without_env_or_dotenv(monkeypatch):
    monkeypatch.delenv("DATA_PROVIDER_API_KEY", raising=False)
    monkeypatch.delenv("VNSTOCK_API_KEY", raising=False)
    config = Settings(_env_file=None)

    assert config.data_provider_api_key.get_secret_value() == ""
    assert config.vnstock_api_key.get_secret_value() == ""
