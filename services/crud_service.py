"""json_storage / quick_search 라이브러리를 활용한 CRUD 서비스."""
from libs.json_storage import JsonStorage
from libs.quick_search import quick_sort, search_by_key


class RecordNotFoundError(Exception):
    """지정한 조건에 해당하는 레코드를 찾지 못했을 때 발생한다."""


class CrudService:
    def __init__(self, file_path):
        self.storage = JsonStorage(file_path)

    def _load_state(self):
        """{"next_id": int, "records": [...]} 형태의 상태를 불러온다.

        next_id는 삭제된 레코드가 있어도 남아있는 레코드의 최대값과 무관하게 계속 증가하는
        채번 카운터로, id 재사용으로 인한 데이터 혼동을 방지한다. 과거에 레코드 리스트만
        저장하던 파일도 그대로 읽을 수 있도록 마이그레이션한다.
        """
        data = self.storage.load(default={"next_id": 1, "records": []})
        if isinstance(data, list):
            existing_ids = [r.get("id", 0) for r in data]
            next_id = (max(existing_ids) + 1) if existing_ids else 1
            data = {"next_id": next_id, "records": data}

        if not isinstance(data, dict) or not isinstance(data.get("records"), list):
            raise ValueError(f"{self.storage.file_path} 파일의 데이터 구조가 올바르지 않습니다.")
        data.setdefault("next_id", 1)

        return data

    def create(self, fields):
        """새 레코드를 생성해 저장하고 반환한다. id는 자동으로 채번되며 fields에 id가 있어도 무시한다."""
        state = self._load_state()
        record = {**fields, "id": state["next_id"]}
        state["records"].append(record)
        state["next_id"] += 1
        self.storage.save(state)
        return record

    def read_all(self):
        """전체 레코드를 id 기준으로 정렬하여 반환한다."""
        return quick_sort(self._load_state()["records"], "id")

    def read_by_id(self, record_id):
        """id로 레코드 하나를 검색한다. 없으면 None을 반환한다."""
        matches = search_by_key(self._load_state()["records"], "id", record_id)
        return matches[0] if matches else None

    def read_by_key(self, key, value):
        """임의의 key=value 조건으로 레코드를 검색한다."""
        return search_by_key(self._load_state()["records"], key, value)

    def update(self, record_id, updated_fields):
        """id로 레코드를 찾아 지정된 필드만 갱신한다. id 필드 자체는 변경되지 않는다."""
        state = self._load_state()
        matches = search_by_key(state["records"], "id", record_id)
        if not matches:
            raise RecordNotFoundError(f"id={record_id} 레코드를 찾을 수 없습니다.")

        target = matches[0]
        target.update(updated_fields)
        target["id"] = record_id
        self.storage.save(state)
        return target

    def delete(self, record_id):
        """id로 레코드를 찾아 안전하게 삭제한다. 대상이 없으면 예외를 발생시켜 실수로 인한 삭제를 방지한다."""
        state = self._load_state()
        matches = search_by_key(state["records"], "id", record_id)
        if not matches:
            raise RecordNotFoundError(f"id={record_id} 레코드를 찾을 수 없습니다.")

        target = matches[0]
        state["records"].remove(target)
        self.storage.save(state)
        return target
