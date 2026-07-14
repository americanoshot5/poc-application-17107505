# PoCApplication

JSON 파일을 데이터 저장소로 사용하는 CRUD 콘솔 애플리케이션입니다. 데이터는 고정된 스키마 없이
자유로운 필드(key=value)로 구성되며, 검색은 quick sort 정렬 후 이진 탐색으로 동작합니다.

## 요구 사항

- Python 3.14 (`.venv`에 이미 구성되어 있음)
- 테스트 실행 시 `pytest` (`requirements-dev.txt` 참고)

## 실행 방법

```bash
.venv/Scripts/python.exe main.py
```

실행하면 아래와 같은 메뉴가 반복해서 표시됩니다.

```
==== JSON CRUD 콘솔 ====
1. 등록 (Create)
2. 전체 조회 (Read All)
3. 검색 (Read by field)
4. 수정 (Update)
5. 삭제 (Delete)
0. 종료
========================
```

- **등록**: `key=value` 형식으로 원하는 만큼 필드를 입력합니다(빈 줄 입력 시 종료). `id`는 자동으로
  채번되며 직접 입력할 수 없습니다.
- **전체 조회**: 저장된 모든 레코드를 `id` 기준으로 정렬해 보여줍니다.
- **검색**: 필드명과 값을 입력하면 해당 조건에 맞는 레코드를 모두 찾아 보여줍니다(`id`로 검색 시
  숫자로 변환).
- **수정**: `id`로 대상을 지정한 뒤 변경할 필드만 `key=value`로 입력합니다. `id` 자체는 변경되지
  않습니다.
- **삭제**: `id`로 대상을 지정하면 삭제 전 대상 레코드를 보여주고 `y/n` 확인을 받은 뒤에만
  삭제합니다.

## 프로젝트 구조

```
PoCApplication/
├── main.py                     # 콘솔 메뉴 및 입출력 처리
├── libs/
│   ├── json_storage.py         # JSON 파일 로드/저장 라이브러리
│   └── quick_search.py         # quick sort 정렬 + 이진 탐색 라이브러리
├── services/
│   └── crud_service.py         # 위 라이브러리를 조합한 CRUD 서비스
├── data/
│   └── records.json            # 실제 데이터 파일
└── tests/                      # pytest 회귀/안전성 테스트
```

## 라이브러리

### `libs/json_storage.py` — `JsonStorage`

임의의 JSON 데이터(리스트, dict 등)를 파일에 저장하고 불러오는 범용 라이브러리입니다.

- `load(default=None)`: 파일이 없거나 비어 있으면 `default`를 반환합니다. JSON 형식이 깨져 있으면
  `ValueError`를 발생시킵니다.
- `save(data)`: 임시 파일(`.tmp`)에 먼저 쓰고 `os.replace`로 원본과 교체하는 방식으로 저장해,
  저장 도중 오류가 나도 기존 파일이 손상되지 않도록 합니다. 저장에 실패하면 남은 임시 파일을
  정리합니다.

### `libs/quick_search.py`

- `quick_sort(records, key)`: 지정한 key 값 기준으로 quick sort 알고리즘을 이용해 정렬된 새
  리스트를 반환합니다(원본 리스트는 변경하지 않음).
- `binary_search(sorted_records, key, value)`: 정렬된 리스트에서 이진 탐색으로 `key == value`인
  레코드를 모두 찾습니다(동일 값이 여러 개면 전부 반환).
- `search_by_key(records, key, value)`: 위 두 함수를 조합해, key 필드를 가진 레코드만 대상으로
  정렬 후 검색하는 실제 검색 API입니다. CRUD 서비스가 이 함수를 사용합니다.

## CRUD 서비스 (`services/crud_service.py`)

`CrudService`는 `JsonStorage`와 `quick_search`를 조합해 CRUD 기능을 제공합니다.

- `create(fields)`: 새 레코드를 만들어 저장합니다. id는 자동 채번되며, `fields`에 `id`가 섞여
  들어와도 무시됩니다.
- `read_all()` / `read_by_id(id)` / `read_by_key(key, value)`
- `update(id, updated_fields)`: 지정한 필드만 갱신하며 `id`는 보호됩니다.
- `delete(id)`: 대상이 없으면 `RecordNotFoundError`를 발생시켜 실수로 인한 삭제를 방지합니다.

### 데이터 파일 형식

```json
{
  "next_id": 3,
  "records": [
    { "id": 1, "name": "Alice", "age": "30" },
    { "id": 2, "name": "Bob", "age": "25" }
  ]
}
```

`next_id`는 삭제된 레코드가 있어도 남은 레코드의 최댓값과 무관하게 계속 증가하는 채번 카운터입니다.
레코드를 삭제해도 그 id는 재사용되지 않아, 이전에 참조하던 id가 다른 레코드를 가리키는 혼동을
방지합니다. (레코드 리스트만 저장하던 이전 형식 파일도 열 때 자동으로 이 형식으로 마이그레이션됩니다.)

## 테스트

```bash
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m pytest tests/ -v
```

`tests/` 에는 각 라이브러리와 CRUD 서비스, 콘솔 핸들러에 대한 회귀 테스트와 함께 다음과 같은
안전성(safety) 테스트가 포함되어 있습니다.

- 저장 도중 오류가 발생해도 기존 데이터 파일이 손상되지 않는지
- 콘솔/서비스 양쪽에서 `id`를 임의로 지정하거나 덮어쓸 수 없는지
- 삭제 시 확인(`y/n`) 없이는 실제로 삭제되지 않는지, 존재하지 않는 id 삭제 시도가 기존 데이터를
  건드리지 않는지
- 삭제된 id가 재사용되지 않는지, 손상되었거나 알 수 없는 구조의 데이터 파일을 안전하게 오류로
  처리하는지
