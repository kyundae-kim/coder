---
name: sqlalchemy-alembic-schema-migration
description: >
  PRD/스펙 변경에 따른 SQLAlchemy ORM + Alembic 마이그레이션 전체 반영 패턴.
  테이블 구조 변경(컬럼 통합, 테이블 제거, 컬럼 rename)을 ORM → DTO → 서비스 → UI → 마이그레이션 순서로 일괄 적용.
triggers:
  - DB 스키마가 변경됐다
  - PRD 보고 코드 반영해줘
  - 테이블 통합 / 컬럼 rename / 테이블 DROP
  - alembic revision 새로 만들어야 함
tags:
  - sqlalchemy
  - alembic
  - schema
  - migration
  - orm
  - streamlit
---

# SQLAlchemy + Alembic 스키마 변경 전체 반영

## 적용 순서 (순서 엄수)

1. **PRD / 스펙 문서 파악**
   - 변경 대상 테이블/컬럼 목록, 타입, nullable 여부 확인
   - 기존 alembic init revision ID 확인 (`alembic/versions/` 파일명)

2. **schema.py (ORM) 수정**
   - 제거 대상 ORM 클래스 삭제
   - 신규 컬럼을 기존 ORM에 추가
   - 컬럼 rename은 ORM 속성명만 변경 (실제 DB rename은 alembic에서)

3. **dto.py 수정**
   - 제거 대상 DTO 클래스 삭제
   - 통합 컬럼 타입 변경 (예: `List[SubDTO]` → `int`)
   - 필드명 rename 반영

4. **service 레이어 수정**
   - 삭제된 DTO/ORM 참조 제거
   - 타입 변경에 따른 비교/연산 로직 수정
     - 예: `jav.score_jadb[-1].score` → `jav.score_jadb` (List → int)
     - 예: `not jav.score_jadb` → `jav.score_jadb == 0` (int 명시 비교)

5. **UI 레이어 수정 (Streamlit pages/app.py)**
   - 이력 관리 UI → 단순 int 입력 폼으로 교체
   - `number_input` 위젯으로 대체

6. **repository (mariadb.py 등) 확인**
   - 삭제된 ORM 참조 잔존 여부 grep으로 확인
   - 없으면 수정 불필요

7. **Alembic 마이그레이션 파일 작성**
   - `down_revision`: 기존 최신 revision ID
   - upgrade(): 데이터 이전 SQL → 구 테이블 DROP → 신규 컬럼 ADD → 컬럼 rename 순서
   - downgrade(): 역순 원복
   - 참고: `references/alembic-migration-template.md`

8. **잔존 참조 grep 검증**
   - 삭제한 ORM/DTO 클래스명으로 전체 검색, 0건 확인

## 핵심 패턴

### 컬럼 rename (alembic)
```python
op.alter_column('테이블명', '기존컬럼명', new_column_name='새컬럼명',
                existing_type=sa.Integer, nullable=False)
```

### 테이블 통합 데이터 이전 (upgrade 내 op.execute)
```python
# 이력 테이블에서 최신값만 이전
op.execute("""
    UPDATE target_table t
    INNER JOIN (
        SELECT fk_id, score FROM source_table
        WHERE (fk_id, dt) IN (SELECT fk_id, MAX(dt) FROM source_table GROUP BY fk_id)
    ) latest ON t.id = latest.fk_id
    SET t.score_col = latest.score
""")
op.drop_table('source_table')
```

### int 타입 score 비교 주의
- `not score` 대신 `score == 0` 명시 — int 0은 falsy이므로 의도치 않은 필터 방지
- sort key: `key=lambda x: x.score_jadb` (단순 int)

## 검증 체크리스트
- [ ] 삭제한 ORM/DTO 클래스명 grep → 0건
- [ ] lint OK (write_file / patch 자동 체크)
- [ ] `alembic upgrade head` dry-run 또는 실행
