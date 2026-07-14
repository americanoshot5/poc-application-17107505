"""quick_search (quick sort + binary search) 회귀/안전성 테스트."""
import pytest

from libs.quick_search import binary_search, quick_sort, search_by_key


def test_quick_sort_sorts_by_key_ascending():
    records = [{"id": 3}, {"id": 1}, {"id": 2}]
    result = quick_sort(records, "id")
    assert [r["id"] for r in result] == [1, 2, 3]


def test_quick_sort_handles_empty_and_single_element_list():
    assert quick_sort([], "id") == []
    assert quick_sort([{"id": 1}], "id") == [{"id": 1}]


def test_quick_sort_does_not_mutate_input_list():
    records = [{"id": 3}, {"id": 1}, {"id": 2}]
    original_order = list(records)

    quick_sort(records, "id")

    assert records == original_order


def test_quick_sort_keeps_all_elements_with_duplicate_keys():
    records = [{"id": 2, "n": "a"}, {"id": 1, "n": "b"}, {"id": 2, "n": "c"}]
    result = quick_sort(records, "id")
    assert [r["id"] for r in result] == [1, 2, 2]
    assert {r["n"] for r in result} == {"a", "b", "c"}


def test_quick_sort_works_with_string_keys():
    records = [{"name": "charlie"}, {"name": "alice"}, {"name": "bob"}]
    result = quick_sort(records, "name")
    assert [r["name"] for r in result] == ["alice", "bob", "charlie"]


def test_binary_search_finds_existing_value():
    sorted_records = [{"id": 1}, {"id": 2}, {"id": 3}]
    result = binary_search(sorted_records, "id", 2)
    assert result == [{"id": 2}]


def test_binary_search_returns_empty_list_when_not_found():
    sorted_records = [{"id": 1}, {"id": 2}, {"id": 3}]
    assert binary_search(sorted_records, "id", 99) == []


def test_binary_search_on_empty_list_returns_empty_list():
    assert binary_search([], "id", 1) == []


def test_binary_search_returns_all_duplicates():
    sorted_records = [{"id": 1, "n": "a"}, {"id": 2, "n": "b"}, {"id": 2, "n": "c"}, {"id": 3, "n": "d"}]
    result = binary_search(sorted_records, "id", 2)
    assert {r["n"] for r in result} == {"b", "c"}


def test_search_by_key_sorts_then_finds(monkeypatch):
    records = [{"id": 3, "age": 30}, {"id": 1, "age": 25}, {"id": 2, "age": 25}]
    result = search_by_key(records, "age", 25)
    assert {r["id"] for r in result} == {1, 2}


def test_search_by_key_ignores_records_missing_the_key():
    records = [{"id": 1, "age": 25}, {"id": 2}]  # id=2 레코드에는 age 필드가 없다
    result = search_by_key(records, "age", 25)
    assert result == [{"id": 1, "age": 25}]


def test_search_by_key_returns_empty_list_when_no_record_has_key():
    records = [{"id": 1}, {"id": 2}]
    assert search_by_key(records, "age", 25) == []
