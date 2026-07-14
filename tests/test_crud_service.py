"""CrudService 회귀/안전성 테스트."""
import pytest

from services.crud_service import CrudService, RecordNotFoundError


@pytest.fixture
def service(tmp_path):
    return CrudService(str(tmp_path / "records.json"))


# ---- Create -----------------------------------------------------------

def test_create_assigns_incrementing_ids(service):
    first = service.create({"name": "Alice"})
    second = service.create({"name": "Bob"})

    assert first["id"] == 1
    assert second["id"] == 2


def test_create_persists_to_file(service):
    service.create({"name": "Alice"})

    reloaded = CrudService(service.storage.file_path)
    assert reloaded.read_all() == [{"id": 1, "name": "Alice"}]


def test_create_ignores_client_supplied_id(service):
    """create의 fields에 id가 섞여 들어와도 자동 채번된 id로 덮어써야 한다."""
    record = service.create({"id": 999, "name": "Alice"})
    assert record["id"] == 1


def test_next_id_continues_from_max_existing_id_even_after_deletion(service):
    service.create({"name": "Alice"})  # id=1
    service.create({"name": "Bob"})    # id=2
    service.delete(2)

    third = service.create({"name": "Carol"})

    assert third["id"] == 3  # 삭제된 id=2를 재사용하지 않는다


# ---- Read ---------------------------------------------------------------

def test_read_all_on_empty_store_returns_empty_list(service):
    assert service.read_all() == []


def test_read_all_returns_records_sorted_by_id(service):
    service.create({"name": "Alice"})
    service.create({"name": "Bob"})

    result = service.read_all()

    assert [r["id"] for r in result] == [1, 2]


def test_read_by_id_returns_matching_record(service):
    service.create({"name": "Alice"})
    service.create({"name": "Bob"})

    result = service.read_by_id(2)

    assert result == {"id": 2, "name": "Bob"}


def test_read_by_id_returns_none_when_missing(service):
    service.create({"name": "Alice"})
    assert service.read_by_id(999) is None


def test_read_by_key_returns_all_matches(service):
    service.create({"name": "Alice", "age": "30"})
    service.create({"name": "Bob", "age": "30"})
    service.create({"name": "Carol", "age": "25"})

    result = service.read_by_key("age", "30")

    assert {r["name"] for r in result} == {"Alice", "Bob"}


def test_read_by_key_returns_empty_list_for_unknown_field(service):
    service.create({"name": "Alice"})
    assert service.read_by_key("unknown_field", "x") == []


# ---- Update ---------------------------------------------------------------

def test_update_modifies_only_specified_fields(service):
    service.create({"name": "Alice", "age": "30"})

    updated = service.update(1, {"age": "31"})

    assert updated == {"id": 1, "name": "Alice", "age": "31"}


def test_update_persists_change(service):
    service.create({"name": "Alice", "age": "30"})
    service.update(1, {"age": "31"})

    reloaded = CrudService(service.storage.file_path)
    assert reloaded.read_by_id(1)["age"] == "31"


def test_update_raises_when_id_not_found(service):
    service.create({"name": "Alice"})
    with pytest.raises(RecordNotFoundError):
        service.update(999, {"age": "31"})


def test_update_does_not_change_id_even_if_requested(service):
    """안전성: update가 id 자체를 변경해 데이터 정합성을 깨뜨리지 않아야 한다."""
    service.create({"name": "Alice"})

    updated = service.update(1, {"id": 999, "name": "Alicia"})

    assert updated["id"] == 1
    assert service.read_by_id(999) is None


def test_update_does_not_affect_other_records(service):
    service.create({"name": "Alice", "age": "30"})
    service.create({"name": "Bob", "age": "25"})

    service.update(1, {"age": "31"})

    assert service.read_by_id(2) == {"id": 2, "name": "Bob", "age": "25"}


# ---- Delete ---------------------------------------------------------------

def test_delete_removes_record(service):
    service.create({"name": "Alice"})
    service.delete(1)

    assert service.read_all() == []


def test_delete_raises_when_id_not_found(service):
    service.create({"name": "Alice"})
    with pytest.raises(RecordNotFoundError):
        service.delete(999)


def test_delete_of_missing_id_does_not_touch_existing_data(service):
    """안전성: 존재하지 않는 id 삭제 시도가 기존 데이터를 훼손하지 않아야 한다."""
    service.create({"name": "Alice"})

    with pytest.raises(RecordNotFoundError):
        service.delete(999)

    assert service.read_all() == [{"id": 1, "name": "Alice"}]


def test_delete_only_removes_the_targeted_record(service):
    service.create({"name": "Alice"})
    service.create({"name": "Bob"})
    service.create({"name": "Carol"})

    service.delete(2)

    remaining_ids = {r["id"] for r in service.read_all()}
    assert remaining_ids == {1, 3}


# ---- Data file compatibility / integrity -----------------------------------

def test_reads_legacy_plain_list_file_and_migrates_next_id(tmp_path):
    """예전 버전(레코드 리스트만 저장)으로 만든 파일도 그대로 읽고, 다음 id는 이어서 채번되어야 한다."""
    file_path = tmp_path / "records.json"
    file_path.write_text('[{"id": 1, "name": "Alice"}, {"id": 5, "name": "Bob"}]', encoding="utf-8")

    service = CrudService(str(file_path))

    assert {r["id"] for r in service.read_all()} == {1, 5}
    new_record = service.create({"name": "Carol"})
    assert new_record["id"] == 6  # 기존 최대 id(5) 다음부터 채번


def test_raises_on_malformed_state_file(tmp_path):
    """레코드 리스트도, {"records": [...]} 구조도 아닌 파일은 안전하게 오류로 처리해야 한다."""
    file_path = tmp_path / "records.json"
    file_path.write_text('{"unexpected": true}', encoding="utf-8")

    service = CrudService(str(file_path))
    with pytest.raises(ValueError):
        service.read_all()
