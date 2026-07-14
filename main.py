"""JSON 파일 기반 CRUD 콘솔 애플리케이션."""
import os

from services.crud_service import CrudService, RecordNotFoundError

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "records.json")

MENU = """
==== JSON CRUD 콘솔 ====
1. 등록 (Create)
2. 전체 조회 (Read All)
3. 검색 (Read by field)
4. 수정 (Update)
5. 삭제 (Delete)
0. 종료
========================"""


def input_fields():
    fields = {}
    print("필드를 'key=value' 형식으로 한 줄에 하나씩 입력하세요. 빈 줄을 입력하면 종료됩니다.")
    while True:
        line = input("> ").strip()
        if not line:
            break
        if "=" not in line:
            print("형식이 올바르지 않습니다. 예) name=홍길동")
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key == "id":
            print("id는 자동으로 관리되므로 직접 입력할 수 없습니다.")
            continue
        fields[key] = value.strip()
    return fields


def print_records(records):
    if not records:
        print("데이터가 없습니다.")
        return
    for record in records:
        print(record)


def handle_create(service):
    fields = input_fields()
    if not fields:
        print("입력된 필드가 없어 등록을 취소합니다.")
        return
    record = service.create(fields)
    print(f"등록 완료: {record}")


def handle_read_all(service):
    print_records(service.read_all())


def handle_search(service):
    key = input("검색할 필드명(id 포함): ").strip()
    value = input("검색할 값: ").strip()
    if key == "id":
        try:
            value = int(value)
        except ValueError:
            print("id는 숫자여야 합니다.")
            return
    results = service.read_by_key(key, value)
    print_records(results)


def handle_update(service):
    try:
        record_id = int(input("수정할 레코드의 id: ").strip())
    except ValueError:
        print("id는 숫자여야 합니다.")
        return

    fields = input_fields()
    if not fields:
        print("수정할 필드가 없어 취소합니다.")
        return

    try:
        record = service.update(record_id, fields)
        print(f"수정 완료: {record}")
    except RecordNotFoundError as e:
        print(e)


def handle_delete(service):
    try:
        record_id = int(input("삭제할 레코드의 id: ").strip())
    except ValueError:
        print("id는 숫자여야 합니다.")
        return

    record = service.read_by_id(record_id)
    if record is None:
        print(f"id={record_id} 레코드를 찾을 수 없습니다.")
        return

    print("삭제 대상:", record)
    confirm = input("정말 삭제하시겠습니까? (y/n): ").strip().lower()
    if confirm != "y":
        print("삭제를 취소했습니다.")
        return

    try:
        service.delete(record_id)
        print("삭제 완료")
    except RecordNotFoundError as e:
        print(e)


def main():
    service = CrudService(DATA_FILE)
    actions = {
        "1": handle_create,
        "2": handle_read_all,
        "3": handle_search,
        "4": handle_update,
        "5": handle_delete,
    }

    while True:
        print(MENU)
        choice = input("선택: ").strip()
        if choice == "0":
            print("종료합니다.")
            break
        action = actions.get(choice)
        if action is None:
            print("올바른 메뉴 번호를 입력하세요.")
            continue
        action(service)


if __name__ == "__main__":
    main()
