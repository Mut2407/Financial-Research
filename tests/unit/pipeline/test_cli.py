import json
import sys

import pytest

import src.pipeline.cli as cli


pytestmark = pytest.mark.unit


def test_parser_requires_a_command():
    with pytest.raises(SystemExit) as error:
        cli.build_parser().parse_args([])

    assert error.value.code == 2


def test_parser_maps_ingest_arguments():
    args = cli.build_parser().parse_args(
        [
            "ingest",
            "--tickers",
            "FPT",
            "VCB",
            "--start",
            "2025-01-01",
            "--end",
            "2025-01-31",
        ]
    )

    assert args.command == "ingest"
    assert args.tickers == ["FPT", "VCB"]
    assert args.interval == "1D"


def test_parser_rejects_non_daily_interval():
    with pytest.raises(SystemExit) as error:
        cli.build_parser().parse_args(
            [
                "ingest",
                "--tickers",
                "FPT",
                "--start",
                "2025-01-01",
                "--end",
                "2025-01-31",
                "--interval",
                "1H",
            ]
        )

    assert error.value.code == 2


def test_ingest_command_connects_source_and_transform(
    monkeypatch, capsys, settings_factory
):
    config = settings_factory()
    calls = []
    monkeypatch.setattr(cli, "get_settings", lambda: config)
    monkeypatch.setattr(
        cli,
        "ingest_tickers",
        lambda tickers, start, end, interval, *, config: calls.append(
            ("ingest", tickers, start, end, interval, config)
        )
        or {"requested": 1, "passed": 1, "failed": 0},
    )
    monkeypatch.setattr(
        cli,
        "transform_raw_data",
        lambda *, input_roots, config: calls.append(("transform", input_roots, config))
        or {"rows": 25, "tickers": 1},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pipeline",
            "ingest",
            "--tickers",
            "FPT",
            "--start",
            "2025-01-01",
            "--end",
            "2025-01-31",
        ],
    )

    cli.main()
    output = json.loads(capsys.readouterr().out)

    assert output["ingestion"]["passed"] == 1
    assert output["transformation"]["rows"] == 25
    assert calls[0][0:5] == ("ingest", ["FPT"], "2025-01-01", "2025-01-31", "1D")
    assert calls[1] == ("transform", [config.raw_path, config.seed_raw_path], config)


def test_transform_command_reads_runtime_raw_only(monkeypatch, capsys, settings_factory):
    config = settings_factory()
    captured = {}
    monkeypatch.setattr(cli, "get_settings", lambda: config)
    monkeypatch.setattr(
        cli,
        "transform_raw_data",
        lambda **kwargs: captured.update(kwargs) or {"rows": 10},
    )
    monkeypatch.setattr(sys, "argv", ["pipeline", "transform"])

    cli.main()

    assert json.loads(capsys.readouterr().out) == {"rows": 10}
    assert captured == {"input_roots": [config.raw_path], "config": config}


def test_bootstrap_skips_when_curated_files_exist(monkeypatch, capsys, settings_factory):
    config = settings_factory()
    curated = config.curated_path / "ticker=FPT" / "part-000.parquet"
    curated.parent.mkdir(parents=True)
    curated.write_bytes(b"existing")
    monkeypatch.setattr(cli, "get_settings", lambda: config)
    monkeypatch.setattr(
        cli,
        "transform_raw_data",
        lambda **kwargs: pytest.fail("existing curated data must not be overwritten by bootstrap"),
    )
    monkeypatch.setattr(sys, "argv", ["pipeline", "bootstrap"])

    cli.main()

    assert json.loads(capsys.readouterr().out) == {
        "status": "skipped",
        "reason": "curated data already exists",
        "files": 1,
    }


def test_bootstrap_uses_runtime_and_seed_roots_when_curated_is_empty(
    monkeypatch, capsys, settings_factory
):
    config = settings_factory()
    captured = {}
    monkeypatch.setattr(cli, "get_settings", lambda: config)
    monkeypatch.setattr(
        cli,
        "transform_raw_data",
        lambda **kwargs: captured.update(kwargs) or {"rows": 25_703},
    )
    monkeypatch.setattr(sys, "argv", ["pipeline", "bootstrap"])

    cli.main()

    assert json.loads(capsys.readouterr().out)["rows"] == 25_703
    assert captured == {
        "input_roots": [config.raw_path, config.seed_raw_path],
        "config": config,
    }
