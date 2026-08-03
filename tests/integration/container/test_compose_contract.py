from pathlib import Path

import pytest
import yaml


pytestmark = [pytest.mark.integration, pytest.mark.container]
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_compose_declares_ordered_vertical_slice():
    compose = yaml.safe_load((PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]

    assert set(services) == {"pipeline", "backend", "frontend"}
    assert services["pipeline"]["command"] == [
        "python",
        "-m",
        "src.pipeline.cli",
        "bootstrap",
    ]
    assert services["backend"]["depends_on"]["pipeline"]["condition"] == (
        "service_completed_successfully"
    )
    assert services["frontend"]["depends_on"]["backend"]["condition"] == "service_healthy"
    assert services["frontend"]["build"]["context"] == "./react-frontend"
    assert services["frontend"]["build"]["dockerfile"] == "Dockerfile"
    assert services["frontend"]["ports"] == ["5173:80"]
    assert services["frontend"]["restart"] == "unless-stopped"
    assert services["pipeline"]["environment"]["DATA_PROVIDER"] == "VNSTOCK_FREE"
    assert services["backend"]["environment"]["VNSTOCK_REQUESTS_PER_MINUTE"] == 60
    assert services["backend"]["healthcheck"]["test"][0:2] == ["CMD", "python"]


def test_container_image_uses_locked_production_dependencies_and_python_312():
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.12-slim" in dockerfile
    assert "RUN uv sync --frozen --no-dev" in dockerfile
    assert "COPY pyproject.toml uv.lock README.md ./" in dockerfile
    assert "COPY src ./src" in dockerfile
    assert "COPY frontend ./frontend" in dockerfile
