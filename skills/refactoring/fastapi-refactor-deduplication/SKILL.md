---
name: fastapi-refactor-deduplication
description: Python 프로젝트(FastAPI/Streamlit 등)에서 중복 코드를 공통 모듈/유틸로 추출하는 리팩토링 패턴
tags: [fastapi, streamlit, refactoring, deduplication, dependencies, python]
triggers:
  - 동일 함수가 여러 라우터/페이지 파일에 복사됨
  - 이슈 심각도 Medium/High로 코드 중복 지적
  - 두 모듈 간 동작 불일치 위험
  - 상태 초기화 보일러플레이트가 여러 페이지에 반복됨
---

# Python 중복 코드 제거 패턴

## 언제 적용하나

- 동일한 헬퍼 함수(예: 사용자명 추출, 권한 확인)가 여러 라우터에 복사되어 있을 때
- 한 곳만 수정될 경우 동작 불일치가 발생할 수 있는 로직
- 이슈에서 "복사", "중복", "한 파일에서만 수정될 경우" 등의 표현이 등장할 때

## 표준 절차

1. **중복 함수 원본 확인**: 두 파일 모두 read_file로 읽어 함수 시그니처와 본문이 실제로 동일한지 확인
2. **공통 위치 결정**: FastAPI 프로젝트에서는 `dependencies/` 모듈이 공통 유틸의 표준 위치
   - 인증/사용자 관련 → `dependencies/security.py`
   - DB/스토리지 관련 → `dependencies/storage.py`
   - 도메인 로직이면 `utils/` 또는 별도 모듈
3. **공통 함수 추출**: 선택한 파일에 함수 추가, docstring으로 우선순위 로직 등 의도 명시
4. **중복 함수 제거 + import 교체**: 각 라우터에서
   - 로컬 함수 정의 삭제
   - import 라인에 새 함수 추가
   - 호출부 전체 교체 (replace_all=True 사용)
5. **검증**: `grep -n "구_함수명\|신_함수명" 관련파일들` 로 잔존 여부 확인

## 핵심 패턴: 사용자명 추출 (이 프로젝트)

이 프로젝트(`docmesh-doc`)는 `preferred_username -> username -> sub` 우선순위 로직을
`docmesh_doc/dependencies/security.py`의 `get_username(user: UserInfo) -> str`로 통합함.
라우터에서는 `from docmesh_doc.dependencies.security import get_username` 후 사용.

## 주의사항 (Pitfalls)

- patch 도구로 함수 제거 시 전후 빈 줄 수를 맞춰야 lint 오류 없음
- `replace_all=True` 없이 동일 패턴 여러 곳 교체 시 첫 번째만 바뀌거나 unique match 오류 발생
- 패치 모드(`mode='patch'`)로 여러 파일 동시 처리 시 한 파일만 적용되는 경우 있음 → 실패한 파일은 별도 replace 모드로 재처리
- 함수 제거 후 빈 router = APIRouter(...) 블록 사이 빈 줄이 2개 이상 남을 수 있음 (lint는 통과하나 스타일 이슈)

## 검증 커맨드

```bash
grep -n "구_함수명\|신_함수명" routes/*.py dependencies/security.py
```

## Streamlit 패턴: 페이지 보일러플레이트 공통화

Streamlit 멀티페이지 앱에서 각 페이지가 동일한 3줄 초기화 코드를 반복할 때:

```python
# 각 pages/*.py 상단 — 반복 패턴
settings = Settings()
conn = st.connection(name=settings.JAVDB, type='sql')
service = JAVService(sess=conn.session)
```

### 해법: pages/common.py 생성

```python
import streamlit as st
from jms.service.javservice import JAVService
from jms.config import Settings

@st.cache_resource
def get_service() -> JAVService:
    settings = Settings()
    conn = st.connection(name=settings.JAVDB, type='sql')
    return JAVService(sess=conn.session)
```

각 페이지에서는:
```python
from pages.common import get_service
service = get_service()
```

- `@st.cache_resource` 로 연결 재사용 (세션 간 캐싱)
- 기존 메서드는 하위 호환을 위해 유지하되 내부에서 공통 메서드에 위임

### 일괄 교체 절차 (execute_code 활용)

1. execute_code로 모든 pages/*.py 상단 패턴 탐지
2. `patch(path, old_block, new_block)` 루프 — old_block은 `\n`으로 구성 (CRLF 파일도 퍼지 매칭으로 처리됨)
3. 교체 후 불필요한 import (JAVService, Settings) 제거 루프 별도 실행

## 메서드 통합 패턴: status별 N개 메서드 → 공통 메서드 + 위임

```python
# 기존 — status마다 복사된 메서드
def update_jav_avdb_by_title(self, javs): ...  # 동일 로직, status='avdb'만 다름
def update_jav_nas_by_title(self, javs): ...
def update_jav_delete_by_title(self, javs): ...

# 리팩토링 — 공통 메서드 + 위임
def update_jav_status_by_id(self, javs, status: str):
    ids = [jav.jav_id for jav in javs]
    javs = self.db.select_jav_all(id=ids)
    for jav in javs:
        jav.status = status
        self.db.update_jav(jav=jav)
    return self.db.select_jav_all(id=ids)

def update_jav_avdb_by_title(self, javs):
    return self.update_jav_status_by_id(javs=javs, status='avdb')
```

호출 사이트가 많을 때는 기존 메서드를 제거하지 말고 위임으로 유지해 하위 호환성 보존.

## IndexError 안티패턴 → 방어 함수

```python
# 안티패턴: try/except로 감추고 raise
try:
    result = some_list[-1].value  # 빈 리스트면 IndexError
except IndexError as e:
    ...
    raise e  # 디버그 코드 섞임

# 방어 함수로 교체
def has_high_score(item) -> bool:
    if not item.score_list:
        return False
    return item.score_list[-1].value >= threshold
```

## 관련 참고

- references/dedup-session-2026-05.md : 실제 세션 예시 (docmesh-doc _current_username 제거)
- references/streamlit-refactor-2026-05.md : Streamlit pages 보일러플레이트 제거 세션
