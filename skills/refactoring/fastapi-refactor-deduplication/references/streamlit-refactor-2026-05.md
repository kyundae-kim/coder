# Streamlit 멀티페이지 리팩토링 세션 (2026-05)

## 프로젝트: /workspaces/jms (Streamlit JAV 관리 앱)

### 문제 상황
- pages/*.py 27개 파일 모두 동일한 3줄 보일러플레이트 반복
- Config 클래스와 Settings 클래스가 공존 (이중화)
- service 메서드가 status별로 4개 복사 (avdb/nas/delete/torrent)
- IndexError를 try/except로 숨기고 raise하는 안티패턴

### 작업 순서

1. Config 클래스 제거 → Settings 일원화 (jms/config.py)
2. pages/common.py 생성 (@st.cache_resource get_service())
3. execute_code 루프로 26개 pages/*.py 보일러플레이트 교체 (2회 패스: 교체 → import 정리)
4. update_jav_status_by_id 공통 메서드 추출, 기존 4개는 위임으로 유지
5. list_playlist_by_type 공통 메서드 추출 (9개 위임)
6. search_jav_for_update: IndexError → high_score() 방어 함수

### execute_code 루프 패턴 (검증됨)

```python
from hermes_tools import patch

old_block = "settings = Settings()\nconn = st.connection(name=settings.JAVDB, type='sql')\nservice = JAVService(sess=conn.session)"
new_block = "from pages.common import get_service\n\n\nservice = get_service()"

for p in pages:
    result = patch(f"/workspaces/jms/pages/{p}.py", old_block, new_block)
    print(f"{p}: {'OK' if result.get('success') else 'FAIL'}")
```

- CRLF 파일도 `\n` 기준 old_block으로 퍼지 매칭 성공
- import 정리는 별도 루프로 분리 실행

### 주의사항

- tag.py는 JAVService를 RDB()와 직접 초기화 — common.py 패턴 적용 불가, 개별 처리
- patch()로 함수 제거 시 해당 범위 내 다른 함수도 포함되면 같이 삭제될 수 있음 (tag.py add_tag 사례)
  → old_string에 최소한의 범위만 포함할 것
