"""main.py 콘솔 핸들러 회귀/안전성 테스트."""
import builtins

import pytest

import main
from services.crud_service import CrudService


@pytest.fixture
def service(tmp_path):
    return CrudService(str(tmp_path / "records.json"))


def make_input(monkeypatch, lines):
    """input() 호출 시 lines를 순서대로 반환하도록 대체한다."""
    iterator = iter(lines)

    def fake_input(prompt=""):
        try:
            return next(iterator)
        except StopIteration as e:
            raise AssertionError("input()이 예상보다 더 많이 호출되었습니다.") from e

    monkeypatch.setattr(builtins, "input", fake_input)


# ---- input_fields ---------------------------------------------------------

def test_input_fields_parses_key_value_lines(monkeypatch):
    make_input(monkeypatch, ["name=Alice", "age=30", ""])
    assert main.input_fields() == {"name": "Alice", "age": "30"}


def test_input_fields_rejects_lines_without_equals(monkeypatch, capsys):
    make_input(monkeypatch, ["invalid_line", "name=Alice", ""])
    fields = main.input_fields()

    assert fields == {"name": "Alice"}
    assert "형식이 올바르지 않습니다" in capsys.readouterr().out


def test_input_fields_blocks_manual_id_assignment(monkeypatch, capsys):
    """안전성: 콘솔에서 id를 직접 지정해 자동 채번을 우회할 수 없어야 한다."""
    make_input(monkeypatch, ["id=999", "name=Alice", ""])
    fields = main.input_fields()

    assert "id" not in fields
    assert "id는 자동으로 관리되므로" in capsys.readouterr().out


# ---- handle_create ----------------------------------------------------------

def test_handle_create_adds_record(monkeypatch, service):
    make_input(monkeypatch, ["name=Alice", ""])
    main.handle_create(service)

    assert service.read_all() == [{"id": 1, "name": "Alice"}]


def test_handle_create_with_no_fields_creates_nothing(monkeypatch, service, capsys):
    make_input(monkeypatch, [""])
    main.handle_create(service)

    assert service.read_all() == []
    assert "취소" in capsys.readouterr().out


# ---- handle_search ----------------------------------------------------------

def test_handle_search_by_id_converts_value_to_int(monkeypatch, service, capsys):
    service.create({"name": "Alice"})
    make_input(monkeypatch, ["id", "1"])

    main.handle_search(service)

    assert "Alice" in capsys.readouterr().out


def test_handle_search_by_id_with_non_numeric_value_reports_error(monkeypatch, service, capsys):
    service.create({"name": "Alice"})
    make_input(monkeypatch, ["id", "not-a-number"])

    main.handle_search(service)

    assert "숫자여야 합니다" in capsys.readouterr().out


# ---- handle_update ----------------------------------------------------------

def test_handle_update_changes_field(monkeypatch, service):
    service.create({"name": "Alice", "age": "30"})
    make_input(monkeypatch, ["1", "age=31", ""])

    main.handle_update(service)

    assert service.read_by_id(1)["age"] == "31"


def test_handle_update_with_non_numeric_id_reports_error_and_changes_nothing(monkeypatch, service, capsys):
    service.create({"name": "Alice", "age": "30"})
    make_input(monkeypatch, ["abc"])

    main.handle_update(service)

    assert "숫자여야 합니다" in capsys.readouterr().out
    assert service.read_by_id(1)["age"] == "30"


def test_handle_update_missing_id_reports_not_found(monkeypatch, service, capsys):
    service.create({"name": "Alice"})
    make_input(monkeypatch, ["999", "name=Ghost", ""])

    main.handle_update(service)

    assert "찾을 수 없습니다" in capsys.readouterr().out


# ---- handle_delete (safety-critical) ---------------------------------------

def test_handle_delete_requires_confirmation(monkeypatch, service):
    """안전성: 삭제 확인에서 'y' 이외의 답변이면 실제로 삭제되지 않아야 한다."""
    service.create({"name": "Alice"})
    make_input(monkeypatch, ["1", "n"])

    main.handle_delete(service)

    assert service.read_all() == [{"id": 1, "name": "Alice"}]


def test_handle_delete_confirmed_removes_record(monkeypatch, service):
    service.create({"name": "Alice"})
    make_input(monkeypatch, ["1", "y"])

    main.handle_delete(service)

    assert service.read_all() == []


def test_handle_delete_shows_target_before_asking_confirmation(monkeypatch, service, capsys):
    """안전성: 사용자가 무엇을 지우는지 먼저 확인할 수 있어야 한다."""
    service.create({"name": "Alice"})
    make_input(monkeypatch, ["1", "n"])

    main.handle_delete(service)

    assert "Alice" in capsys.readouterr().out


def test_handle_delete_missing_id_does_not_prompt_for_confirmation(monkeypatch, service):
    """안전성: 존재하지 않는 id는 확인 질문 없이 즉시 실패해야 한다(불필요한 input 호출 없음)."""
    make_input(monkeypatch, ["999"])  # 확인용 입력을 주지 않아도 통과해야 한다
    main.handle_delete(service)  # input()이 추가로 호출되면 make_input이 AssertionError를 던진다


def test_handle_delete_with_non_numeric_id_reports_error(monkeypatch, service):
    make_input(monkeypatch, ["abc"])
    main.handle_delete(service)  # 예외 없이 처리되어야 한다


# ---- full menu loop (regression) -------------------------------------------

def test_main_end_to_end_menu_flow(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(main, "DATA_FILE", str(tmp_path / "records.json"))
    inputs = [
        "1", "name=Alice", "age=30", "",   # create
        "2",                               # read all
        "4", "1", "age=31", "",            # update
        "5", "1", "y",                     # delete
        "2",                               # read all -> empty
        "0",                                # exit
    ]
    make_input(monkeypatch, inputs)

    main.main()

    out = capsys.readouterr().out
    assert "등록 완료" in out
    assert "수정 완료" in out
    assert "삭제 완료" in out
    assert "종료합니다" in out


def test_main_rejects_invalid_menu_choice(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(main, "DATA_FILE", str(tmp_path / "records.json"))
    make_input(monkeypatch, ["9", "0"])

    main.main()

    assert "올바른 메뉴 번호를 입력하세요" in capsys.readouterr().out
