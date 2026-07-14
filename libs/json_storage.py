"""JSON 파일 입출력을 담당하는 저장소 라이브러리."""
import json
import os


class JsonStorage:
    """지정된 경로의 JSON 파일에 임의의 JSON 데이터를 저장하고 불러온다."""

    def __init__(self, file_path):
        self.file_path = file_path

    def load(self, default=None):
        """JSON 파일을 읽어 반환한다. 파일이 없거나 비어 있으면 default를 반환한다."""
        if not os.path.exists(self.file_path):
            return default

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            return default

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"{self.file_path} 파일의 JSON 형식이 올바르지 않습니다: {e}") from e

    def save(self, data):
        """data를 JSON으로 직렬화하여 파일에 저장한다. 임시 파일에 먼저 쓰고 교체하여 저장 도중
        오류로 기존 파일이 손상되지 않도록 한다."""
        directory = os.path.dirname(self.file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        tmp_path = f"{self.file_path}.tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.file_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
