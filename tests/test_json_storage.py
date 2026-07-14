"""json_storage.JsonStorage 회귀/안전성 테스트."""
import json
import os

import pytest

from libs.json_storage import JsonStorage


def test_load_returns_none_by_default_when_file_missing(tmp_path):
    storage = JsonStorage(str(tmp_path / "missing.json"))
    assert storage.load() is None


def test_load_returns_given_default_when_file_missing(tmp_path):
    storage = JsonStorage(str(tmp_path / "missing.json"))
    assert storage.load(default=[]) == []


def test_load_returns_default_when_file_is_blank(tmp_path):
    file_path = tmp_path / "blank.json"
    file_path.write_text("", encoding="utf-8")

    storage = JsonStorage(str(file_path))
    assert storage.load(default=[]) == []


def test_save_then_load_round_trip(tmp_path):
    file_path = tmp_path / "records.json"
    storage = JsonStorage(str(file_path))
    records = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

    storage.save(records)

    assert storage.load() == records


def test_save_preserves_non_ascii_characters(tmp_path):
    file_path = tmp_path / "records.json"
    storage = JsonStorage(str(file_path))
    records = [{"id": 1, "name": "홍길동"}]

    storage.save(records)

    raw = file_path.read_text(encoding="utf-8")
    assert "홍길동" in raw  # ensure_ascii=False 로 유니코드 이스케이프 없이 저장되어야 한다
    assert storage.load() == records


def test_save_then_load_round_trip_with_dict_payload(tmp_path):
    """JsonStorage는 리스트뿐 아니라 임의의 JSON 구조(dict 등)도 그대로 다룰 수 있어야 한다."""
    file_path = tmp_path / "state.json"
    storage = JsonStorage(str(file_path))
    state = {"next_id": 3, "records": [{"id": 1}, {"id": 2}]}

    storage.save(state)

    assert storage.load() == state


def test_save_creates_parent_directory(tmp_path):
    file_path = tmp_path / "nested" / "dir" / "records.json"
    storage = JsonStorage(str(file_path))

    storage.save([{"id": 1}])

    assert file_path.exists()


def test_load_raises_on_invalid_json(tmp_path):
    file_path = tmp_path / "broken.json"
    file_path.write_text("{not valid json]", encoding="utf-8")

    storage = JsonStorage(str(file_path))
    with pytest.raises(ValueError):
        storage.load()


def test_save_does_not_leave_temp_file_behind(tmp_path):
    file_path = tmp_path / "records.json"
    storage = JsonStorage(str(file_path))

    storage.save([{"id": 1}])

    assert not os.path.exists(f"{file_path}.tmp")


def test_save_failure_does_not_corrupt_existing_file(tmp_path, monkeypatch):
    """저장 도중 오류가 발생해도 임시 파일에만 쓰기 때문에 기존 파일은 그대로 남아야 한다(안전성)."""
    file_path = tmp_path / "records.json"
    storage = JsonStorage(str(file_path))
    storage.save([{"id": 1, "name": "Original"}])

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(json, "dump", boom)

    with pytest.raises(OSError):
        storage.save([{"id": 2, "name": "Corrupted"}])

    # 원본 파일은 손상되지 않고 이전 내용을 그대로 유지해야 한다.
    assert storage.load() == [{"id": 1, "name": "Original"}]
    assert not os.path.exists(f"{file_path}.tmp")
