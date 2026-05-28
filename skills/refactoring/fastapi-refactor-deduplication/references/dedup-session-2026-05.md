# 실사례: docmesh-doc _current_username 중복 제거 (2026-05)

## 이슈
- 심각도: Medium
- `_current_username` 함수가 `routes/documents.py:16`과 `routes/metadata.py:14`에 동일하게 복사됨
- `preferred_username -> username -> sub` 우선순위 로직이 한 파일에서만 수정될 경우 동작 불일치 위험

## 해결책
`docmesh_doc/dependencies/security.py`에 공통 함수 추가:

```python
def get_username(user: UserInfo) -> str:
    """preferred_username -> username -> sub 우선순위로 사용자 이름을 반환합니다."""
    username = getattr(user, "preferred_username", None) or getattr(user, "username", None)
    return username or user.sub
```

## 교체 범위
- documents.py: 3곳 (`upload_document`, 기타 핸들러)
- metadata.py: 4곳 (`create_metadata`, 기타 핸들러)

## 트러블슈팅
- `mode='patch'`로 두 파일 동시 처리 시 metadata.py에 미적용 → 별도 replace 모드로 재처리
- `replace_all=True`로 호출부 일괄 교체 성공
