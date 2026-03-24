import json
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
migrate_artifact = getattr(migrate_json_to_mongo, "_migrate_artifact")
save_artifact_data = getattr(migrate_json_to_mongo, "_save_artifact_data")
ArtifactSpec = getattr(migrate_json_to_mongo, "_ArtifactSpec")


# ============================================================
# Helpers
# ============================================================


class _FakeRepo:
    """Minimal mock that records save calls and optionally fails."""

    def __init__(self, existing=None, fail_on_call: int = 0):
        self.saved: list = []
        self.existing = existing
        self._fail_on_call = fail_on_call
        self._call_count = 0

    def save(self, data):
        self._call_count += 1
        if self._fail_on_call and self._call_count == self._fail_on_call:
            raise RuntimeError("Simulated failure")
        self.saved.append(data)

    def get_existing(self):
        return self.existing


_SINGLE_SPEC = ArtifactSpec(
    filename="test.json",
    expected_type=dict,
    count_key="test",
    save_method="save",
    label="test",
)

_MULTI_SPEC = ArtifactSpec(
    filename="test.json",
    expected_type=list,
    count_key="test",
    save_method="save",
    label="test",
    multi_record=True,
)

_REPLACE_SPEC = ArtifactSpec(
    filename="test.json",
    expected_type=dict,
    count_key="test",
    save_method="save",
    label="test",
    replace_getter="get_existing",
    replace_checker=lambda data: data == {"default": True},
    replace_label="test (replaced)",
    replace_action="migrated_replaced",
)


def _write_json(path: Path, data) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


# ============================================================
# Path Resolution Tests
# ============================================================


def test_resolve_output_dirs_includes_legacy_and_deduplicates(
    monkeypatch, tmp_path: Path
):
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


# ============================================================
# Payload Validation Tests
# ============================================================


def test_is_default_settings_payload_detects_modified_values():
    defaults = dict(getattr(migrate_json_to_mongo, "_DEFAULT_SETTINGS_PAYLOAD"))

    assert is_default_settings_payload(defaults)

    modified = dict(defaults)
    modified["hide_browser"] = True
    assert not is_default_settings_payload(modified)


def test_is_default_settings_payload_rejects_legacy_browser_key():
    legacy_defaults = dict(getattr(migrate_json_to_mongo, "_DEFAULT_SETTINGS_PAYLOAD"))
    legacy_defaults["open_web_ui"] = legacy_defaults.pop("show_window_on_startup")

    assert not is_default_settings_payload(legacy_defaults)


def test_is_blank_account_payload_requires_credentials():
    assert is_blank_account_payload(
        {"username": "", "password": "", "app_password": ""}
    )
    assert not is_blank_account_payload(
        {"username": "user@example.com", "password": "", "app_password": ""}
    )
    # hoyo_username alone counts as non-blank
    assert not is_blank_account_payload(
        {"username": "", "app_password": "", "hoyo_username": "hoyouser"}
    )
    # hoyo_password alone counts as non-blank
    assert not is_blank_account_payload(
        {"username": "", "app_password": "", "hoyo_password": "secret"}
    )


def test_is_blank_account_payload_non_dict():
    assert is_blank_account_payload(None)
    assert is_blank_account_payload("not a dict")
    assert is_blank_account_payload([])


# ============================================================
# Single-Doc Artifact Migration Tests
# ============================================================


def test_migrate_artifact_single_doc_fresh(tmp_path: Path):
    """Empty collection → migrate single-doc artifact."""
    path = _write_json(tmp_path / "test.json", {"key": "value"})
    repo = _FakeRepo()
    migrated: list[str] = []

    status = migrate_artifact(
        _SINGLE_SPEC, repo, path, before_count=0, migrated=migrated
    )

    assert status["read_ok"] is True
    assert status["action"] == "migrated"
    assert status["safe_to_delete"] is True
    assert repo.saved == [{"key": "value"}]
    assert migrated == ["test"]


def test_migrate_artifact_skips_existing(tmp_path: Path):
    """Populated collection → skip migration."""
    path = _write_json(tmp_path / "test.json", {"key": "value"})
    repo = _FakeRepo()
    migrated: list[str] = []

    status = migrate_artifact(
        _SINGLE_SPEC, repo, path, before_count=1, migrated=migrated
    )

    assert status["action"] == "skipped_existing_data"
    assert status["safe_to_delete"] is True
    assert repo.saved == []
    assert migrated == []


def test_migrate_artifact_missing_file(tmp_path: Path):
    """Missing JSON file → skip with skipped_missing."""
    path = str(tmp_path / "nonexistent.json")
    repo = _FakeRepo()
    migrated: list[str] = []

    status = migrate_artifact(
        _SINGLE_SPEC, repo, path, before_count=0, migrated=migrated
    )

    assert status["action"] == "skipped_missing"
    assert status["read_ok"] is False
    assert status["safe_to_delete"] is False
    assert migrated == []


def test_migrate_artifact_invalid_type(tmp_path: Path):
    """Wrong JSON type → skip with error."""
    path = _write_json(tmp_path / "test.json", [1, 2, 3])
    repo = _FakeRepo()
    migrated: list[str] = []

    status = migrate_artifact(
        _SINGLE_SPEC, repo, path, before_count=0, migrated=migrated
    )

    assert status["action"] == "skipped_invalid"
    assert "Invalid type" in status["parse_error"]
    assert status["safe_to_delete"] is False


def test_migrate_artifact_malformed_json(tmp_path: Path):
    """Broken JSON → skip with parse error."""
    bad_file = tmp_path / "test.json"
    bad_file.parent.mkdir(parents=True, exist_ok=True)
    bad_file.write_text("{invalid json", encoding="utf-8")
    repo = _FakeRepo()
    migrated: list[str] = []

    status = migrate_artifact(
        _SINGLE_SPEC, repo, str(bad_file), before_count=0, migrated=migrated
    )

    assert status["action"] == "skipped_invalid"
    assert status["parse_error"] is not None
    assert status["safe_to_delete"] is False


# ============================================================
# Replace Logic Tests
# ============================================================


def test_migrate_artifact_replaces_default(tmp_path: Path):
    """Existing default data → replace with JSON file data."""
    path = _write_json(tmp_path / "test.json", {"key": "custom"})
    repo = _FakeRepo(existing={"default": True})
    migrated: list[str] = []

    status = migrate_artifact(
        _REPLACE_SPEC, repo, path, before_count=1, migrated=migrated
    )

    assert status["action"] == "migrated_replaced"
    assert status["safe_to_delete"] is True
    assert repo.saved == [{"key": "custom"}]
    assert migrated == ["test (replaced)"]


def test_migrate_artifact_keeps_custom_existing(tmp_path: Path):
    """Existing non-default data → skip replacement."""
    path = _write_json(tmp_path / "test.json", {"key": "new"})
    repo = _FakeRepo(existing={"custom": "data"})
    migrated: list[str] = []

    status = migrate_artifact(
        _REPLACE_SPEC, repo, path, before_count=1, migrated=migrated
    )

    assert status["action"] == "skipped_existing_data"
    assert repo.saved == []
    assert migrated == []


# ============================================================
# Multi-Record Artifact Migration Tests
# ============================================================


def test_migrate_artifact_multi_record(tmp_path: Path):
    """Empty collection → migrate all records."""
    records = [{"day": 1}, {"day": 2}, {"day": 3}]
    path = _write_json(tmp_path / "test.json", records)
    repo = _FakeRepo()
    migrated: list[str] = []

    status = migrate_artifact(
        _MULTI_SPEC, repo, path, before_count=0, migrated=migrated
    )

    assert status["action"] == "migrated"
    assert status["safe_to_delete"] is True
    assert repo.saved == records
    assert migrated == ["test (3 records)"]


def test_migrate_artifact_multi_record_partial_failure(tmp_path: Path):
    """One record fails → report partial migration."""
    records = [{"day": 1}, {"day": 2}, {"day": 3}]
    path = _write_json(tmp_path / "test.json", records)
    repo = _FakeRepo(fail_on_call=2)
    migrated: list[str] = []

    status = migrate_artifact(
        _MULTI_SPEC, repo, path, before_count=0, migrated=migrated
    )

    assert status["action"] == "migrated_partial"
    assert status["records_failed"] == 1
    assert len(repo.saved) == 2
    assert migrated == ["test (2/3 records)"]


# ============================================================
# _save_artifact_data Tests
# ============================================================


def test_save_artifact_data_single(tmp_path: Path):
    repo = _FakeRepo()
    migrated: list[str] = []
    status: dict = {"action": None}

    save_artifact_data(_SINGLE_SPEC, repo, {"x": 1}, migrated, status)

    assert status["action"] == "migrated"
    assert repo.saved == [{"x": 1}]
    assert migrated == ["test"]


def test_save_artifact_data_multi_all_succeed():
    repo = _FakeRepo()
    migrated: list[str] = []
    status: dict = {"action": None}

    save_artifact_data(_MULTI_SPEC, repo, [{"a": 1}, {"b": 2}], migrated, status)

    assert status["action"] == "migrated"
    assert "records_failed" not in status
    assert migrated == ["test (2 records)"]


def test_save_artifact_data_multi_all_fail():
    class AlwaysFailRepo:
        def save(self, data):
            raise RuntimeError("fail")

    migrated: list[str] = []
    status: dict = {"action": None}

    save_artifact_data(
        _MULTI_SPEC, AlwaysFailRepo(), [{"a": 1}, {"b": 2}], migrated, status
    )

    assert status["action"] == "migrated_partial"
    assert status["records_failed"] == 2
    assert migrated == ["test (0/2 records)"]

