import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import utils.migrate_json_to_mongo as migrate_json_to_mongo

resolve_output_dirs = getattr(migrate_json_to_mongo, "_resolve_output_dirs")
resolve_artifact_path = getattr(migrate_json_to_mongo, "_resolve_artifact_path")
is_default_settings_payload = getattr(
    migrate_json_to_mongo, "_is_default_settings_payload"
)
is_blank_account_payload = getattr(migrate_json_to_mongo, "_is_blank_account_payload")


def test_resolve_output_dirs_includes_legacy_and_deduplicates(monkeypatch, tmp_path: Path):
    primary_output = tmp_path / "Programs" / "ZZZ Bot" / "output"
    custom_legacy = tmp_path / "custom-legacy" / "output"

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv(
        "ZZZ_LEGACY_OUTPUT_DIRS",
        f"{custom_legacy};{custom_legacy}",
    )

    resolved = resolve_output_dirs(str(primary_output))

    assert resolved[0] == primary_output
    assert (tmp_path / "zzz-bot" / "output") in resolved
    assert custom_legacy in resolved
    assert resolved.count(custom_legacy) == 1


def test_resolve_artifact_path_prefers_existing_legacy_file(tmp_path: Path):
    primary_output = tmp_path / "Programs" / "ZZZ Bot" / "output"
    legacy_output = tmp_path / "zzz-bot" / "output"
    legacy_output.mkdir(parents=True, exist_ok=True)

    legacy_file = legacy_output / "settings.json"
    legacy_file.write_text("{}", encoding="utf-8")

    resolved_path = resolve_artifact_path(
        "settings.json",
        [primary_output, legacy_output],
    )

    assert resolved_path == str(legacy_file)


def test_is_default_settings_payload_detects_modified_values():
    defaults = dict(getattr(migrate_json_to_mongo, "_DEFAULT_SETTINGS_PAYLOAD"))

    assert is_default_settings_payload(defaults)

    modified = dict(defaults)
    modified["hide_browser"] = True
    assert not is_default_settings_payload(modified)


def test_is_blank_account_payload_requires_credentials():
    assert is_blank_account_payload({"username": "", "password": "", "app_password": ""})
    assert not is_blank_account_payload(
        {"username": "user@example.com", "password": "", "app_password": ""}
    )
