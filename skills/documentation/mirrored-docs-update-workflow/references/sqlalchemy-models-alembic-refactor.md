# SQLAlchemy Models 분리 + Alembic 초기화 패턴

## 배경

`services/metadata.py` 내부에 로컬 `Base(DeclarativeBase)`와 ORM 모델을 선언하는 패턴은
PRD/API 문서에서 "공통 Base 클래스는 `models/base.py` 한 곳에서 선언"하라는 요구가 추가될 때 리팩터링 대상이 된다.

## 결과 디렉터리 구조

```
docmesh_doc/
  models/
    __init__.py     # 모델 외부 노출 (DocumentMetadataModel 등)
    base.py         # 공통 Base(DeclarativeBase) 선언
    metadata.py     # DocumentMetadataModel — base.Base 상속
  services/
    metadata.py     # 로컬 Base/Model 제거, models.* import로 교체
alembic/
  env.py
  versions/
alembic.ini
```

## models/base.py

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

## models/metadata.py

```python
from docmesh_doc.models.base import Base

class DocumentMetadataModel(Base):
    __tablename__ = "document_metadata"
    # ... columns ...
```

## models/__init__.py

```python
from docmesh_doc.models.metadata import DocumentMetadataModel
__all__ = ["DocumentMetadataModel"]
```

## services/metadata.py 변경점

- `class Base(DeclarativeBase): pass` 및 `class DocumentMetadataModel(Base): ...` 제거
- 상단에 추가:
  ```python
  from docmesh_doc.models.base import Base
  from docmesh_doc.models.metadata import DocumentMetadataModel
  ```
- `Base.metadata.create_all(self._engine)` 는 개발 환경용으로 그대로 유지

## Alembic 초기화 절차

```bash
uv run alembic init alembic
```

## alembic/env.py 핵심 설정

```python
from docmesh_doc.models.base import Base
from docmesh_doc.models import metadata  # noqa: F401 (Base에 모델 등록)

target_metadata = Base.metadata

def _get_db_url() -> str:
    host = os.environ.get("DB__HOST", "localhost")
    port = os.environ.get("DB__PORT", "5432")
    name = os.environ.get("DB__NAME", "docmesh")
    user = os.environ.get("DB__USER", "postgres")
    password = os.environ.get("DB__PASSWORD", "postgres")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
```

- `ini_section`에 `sqlalchemy.url`이 없으면 `_get_db_url()`로 환경변수에서 구성
- offline/online 양쪽 모두 처리

## 마이그레이션 명령

```bash
uv run alembic revision --autogenerate -m "initial schema"
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic current
```

## 주의사항

- `autogenerate`가 동작하려면 env.py에서 모든 모델 파일을 import해야 Base에 등록된다.
- `models/__init__.py`에서 import해도 되고, env.py에서 직접 import해도 된다.
- `create_all()`은 개발 환경 전용; 프로덕션은 Alembic만 사용.
