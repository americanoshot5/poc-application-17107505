"""json_storage / quick_search 라이브러리를 활용한 CRUD 서비스."""
from libs.json_storage import JsonStorage
from libs.quick_search import quick_sort, search_by_key


class RecordNotFoundError(Exception):
    """지정한 조건에 해당하는 레코드를 찾지 못했을 때 발생한다."""


class CrudService:
    def __init__(self, file_path):
        self.storage = JsonStorage(file_path)

    def create(self, fields):
        """새 레코드를 생성해 저장하고 반환한다. id는 자동으로 채번된다."""
        records = self.storage.load()
        record = {"id": self._next_id(records), **fields}
        records.append(record)
        self.storage.save(records)
        return record

    def read_all(self):
        """전체 레코드를 id 기준으로 정렬하여 반환한다."""
        records = self.storage.load()
        return quick_sort(records, "id")

    def read_by_id(self, record_id):
        """id로 레코드 하나를 검색한다. 없으면 None을 반환한다."""
        records = self.storage.load()
        matches = search_by_key(records, "id", record_id)
        return matches[0] if matches else None

    def read_by_key(self, key, value):
        """임의의 key=value 조건으로 레코드를 검색한다."""
        records = self.storage.load()
        return search_by_key(records, key, value)

    def update(self, record_id, updated_fields):
        """id로 레코드를 찾아 지정된 필드만 갱신한다. id 필드 자체는 변경되지 않는다."""
        records = self.storage.load()
        matches = search_by_key(records, "id", record_id)
        if not matches:
            raise RecordNotFoundError(f"id={record_id} 레코드를 찾을 수 없습니다.")

        target = matches[0]
        target.update(updated_fields)
        target["id"] = record_id
        self.storage.save(records)
        return target

    def delete(self, record_id):
        """id로 레코드를 찾아 안전하게 삭제한다. 대상이 없으면 예외를 발생시켜 실수로 인한 삭제를 방지한다."""
        records = self.storage.load()
        matches = search_by_key(records, "id", record_id)
        if not matches:
            raise RecordNotFoundError(f"id={record_id} 레코드를 찾을 수 없습니다.")

        target = matches[0]
        records.remove(target)
        self.storage.save(records)
        return target

    @staticmethod
    def _next_id(records):
        if not records:
            return 1
        return max(r.get("id", 0) for r in records) + 1
