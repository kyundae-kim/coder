---
name: streamlit-service-layer-wiring
description: Streamlit UI 위젯 파라미터를 서비스/레포지토리 레이어까지 연결하는 패턴 — 단일값 → 리스트 확장, 기본값 보존, 필터 로직 수정
tags: [streamlit, service-layer, python, refactoring, jms]
---

# Streamlit → Service Layer 파라미터 연결 패턴

## 트리거 조건

- Streamlit 위젯의 입력값(단일 → 리스트 등)이 서비스 메서드에 전달되지 않는 경우
- UI에서 추가된 파라미터가 서비스 로직에 반영되지 않고 고정값(cfg 등)을 사용하는 경우
- 단일 값 위젯을 다중 선택 위젯으로 확장해야 할 때

## 작업 순서

1. **현재 UI 파악**: 해당 page 파일에서 위젯 정의와 서비스 호출부 확인
2. **서비스 메서드 시그니처 확인**: 고정값(cfg.*) 사용 여부 파악
3. **서비스 수정**: 파라미터 추가, 기본값은 기존 cfg 값으로 설정 (하위 호환 유지)
4. **UI 수정**: 위젯 교체 후 서비스 호출 시 파라미터 전달
5. **필터 로직 수정**: 단일 조건 → 리스트 기반 조건(`any(...)`)으로 변경

## 단일값 → 리스트 확장 패턴

### 서비스 레이어

```python
# Before
def add_playlist_etc(self):
    prelist = [play for play in ... if days < self.cfg.ETC_EXCLUED_PLAYLIST * 7 ...]

# After
def add_playlist_etc(self, exclude_weeks: list[int] | None = None):
    if exclude_weeks is None:
        exclude_weeks = [self.cfg.ETC_EXCLUED_PLAYLIST]  # 기존 기본값 보존
    prelist = [
        play for play in ...
        if any(days < w * 7 for w in exclude_weeks) ...  # any()로 리스트 조건
    ]
```

### UI 레이어

```python
# Before: 단일 number_input
exclude_week = st.number_input(label='제외 플레이리스트(W)', min_value=1, max_value=52, value=3, step=1)

# After: multiselect (직접 1~52 범위 옵션 제공)
exclude_weeks = st.multiselect(
    label='제외 플레이리스트(W) 목록',
    options=list(range(1, 53)),
    default=[3],  # 기존 기본값 유지
)

# 서비스 호출 시 빈 리스트면 None 전달 (서비스의 기본값 사용)
service.add_playlist_etc(exclude_weeks=exclude_weeks if exclude_weeks else None)
```

## 주의사항 (Pitfalls)

- **st.button + st.rerun() + multiselect 조합 주의**: 버튼 클릭 → rerun 시 multiselect 상태가 초기화됨. session_state 없이는 rerun으로 multiselect 값을 동적으로 추가하는 패턴이 동작하지 않음. multiselect 단독 사용이 더 안정적.
- **하위 호환 유지**: 서비스 메서드에 파라미터 추가 시 반드시 `None` 기본값 + cfg 폴백으로 기존 동작 보존.
- **빈 리스트 처리**: UI에서 아무것도 선택 안 했을 때 빈 리스트 `[]`가 오면 필터가 전혀 안 걸릴 수 있음. `if exclude_weeks else None` 패턴으로 서비스 기본값에 위임.

## 관련 파일 (JMS 프로젝트)

- pages/playlist_etc.py — UI 위젯 정의
- jms/service/javservice.py — 서비스 레이어 메서드
- jms/repository/rdb/const.py — 플레이리스트 타입 상수
