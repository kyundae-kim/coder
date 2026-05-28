---
name: fastapi-refactor-deduplication
description: FastAPI 프로젝트에서 중복 코드를 공통 의존성/유틸로 추출하는 리팩토링 패턴
tags: [fastapi, refactoring, deduplication, dependencies, python]
triggers:
  - 동일 함수가 여러 라우터 파일에 복사됨
  - 이슈 심각도 Medium/High로 코드 중복 지적
  - 두 라우터 간 동작 불일치 위험
---

# FastAPI 중복 코드 제거 패턴

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

## 관련 참고

- references/dedup-session-2026-05.md : 실제 세션 예시 (docmesh-doc _current_username 제거)
