---
name: fastapi-async-testing
description: FastAPI 프로젝트에서 비동기 테스트 작성 — anyio 내장 pytest 플러그인, NATS/외부 서비스 통합 테스트 패턴, TestClient 이벤트 루프 충돌 해결
tags: [fastapi, pytest, anyio, async, nats, integration-test]
---

# FastAPI 비동기 테스트 패턴

## 트리거 조건
- FastAPI 프로젝트에서 `async def` 테스트 작성
- NATS, DB, MinIO 등 외부 서비스 연동 통합 테스트 추가
- pytest에서 비동기 테스트 지원 여부 확인 요청

## 핵심 설정 — anyio 내장 pytest 플러그인

`pytest-asyncio` 없이도 `anyio >= 4.x`가 설치되어 있으면 비동기 테스트를 직접 실행할 수 있다.

`pyproject.toml`에 한 줄 추가:

```toml
[tool.pytest.ini_options]
anyio_mode = "auto"
```

이 설정으로 `async def test_*` 함수가 자동으로 `[asyncio]` 백엔드에서 실행된다.
별도 마커(`@pytest.mark.anyio`)도 불필요하다.

## async 테스트 기본 패턴

```python
async def test_something():
    result = await some_async_function()
    assert result == expected
```

fixture도 async 가능:

```python
@pytest.fixture
async def nats_client(config):
    nc = await create_nats_client(config.nats)
    yield nc
    await nc.drain()
```

## NATS 통합 테스트 패턴

```python
@pytest.mark.integration
async def test_publish_subscribe_round_trip(nats_config):
    received = []

    async def cb(data: dict) -> None:
        received.append(data)

    nc = await create_nats_client(nats_config)
    try:
        await subscribe_json(nc, "test.topic", cb)
        await publish_json(nc, "test.topic", {"key": "value"})
        await anyio.sleep(0.3)  # 수신 대기
    finally:
        await nc.drain()

    assert received == [{"key": "value"}]
```

queue group 분산 수신 검증:
```python
# 구독자 2개 등록, 4개 메시지 발행 후 총합 확인
await subscribe_json(nc, "test.queue", cb_a, queue="my-group")
await subscribe_json(nc, "test.queue", cb_b, queue="my-group")
# 각 소비자 >= 1, 합계 == 4 검증
```

## TestClient와 async 테스트 충돌 — 중요 pitfall

`TestClient`는 내부적으로 자체 이벤트 루프를 생성한다.
async 테스트 함수 안에서 `TestClient`를 쓰면 루프 충돌이 발생한다.

**해결책**: TestClient를 사용하는 테스트는 동기(`def`)로 유지하고,
NATS 클라이언트는 lifespan을 통해 TestClient 내부 루프에서 생성한다.

```python
# 올바른 패턴: TestClient 테스트는 동기 def
def test_endpoint_via_depends(config):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await set_nats_client(app, config=config)
        yield
        await app.state.nats_client.drain()

    app = FastAPI(lifespan=lifespan)

    @app.get("/check")
    async def check(nc = Depends(get_nats_client)):
        return {"connected": nc.is_connected}

    with TestClient(app) as http:
        response = http.get("/check")
    assert response.json()["connected"] is True
```

module 스코프 fixture로 NATS 클라이언트를 공유하고 TestClient와 함께 쓰면
teardown 시 `nats.errors.FlushTimeoutError`가 발생한다. 각 테스트가 자신의
루프에서 클라이언트를 생성/소멸해야 한다.

## 통합 테스트 마커 설정

```toml
[tool.pytest.ini_options]
markers = ["integration: mark test as integration test (requires external services)"]
```

실행:
```bash
uv run pytest -m integration          # 통합 테스트만
uv run pytest --ignore=test_*_integration.py  # 통합 제외
```

## 파일 구조 규칙 (이 프로젝트)

```
test_fastapi_core/
  core/
    test_messaging.py              # 단위 테스트 (mock 사용)
    test_messaging_integration.py  # 통합 테스트 (실제 서비스)
  dependencies/
    test_messaging.py
    test_messaging_integration.py
```

## 참고 파일
- references/nats-integration-pitfalls.md
