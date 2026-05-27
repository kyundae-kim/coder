# NATS 통합 테스트 — 발견된 pitfall 목록

## 1. module 스코프 fixture + TestClient = FlushTimeoutError

**증상**: fixture teardown에서 `nats.errors.FlushTimeoutError: nats: flush timeout` 발생.
8개 테스트는 모두 PASSED이지만 ERROR 1개 추가.

**원인**: module 스코프 fixture가 anyio.run()으로 클라이언트를 생성 → 이후
TestClient가 자체 이벤트 루프 내에서 같은 클라이언트를 사용 → teardown 시
fixture의 루프(이미 종료)에서 drain() 호출 → 타임아웃.

**해결**: TestClient를 쓰는 테스트는 lifespan 안에서 클라이언트를 생성·소멸.
module 스코프로 공유하지 않는다.

## 2. anyio.run() 래퍼 안에서 lambda 콜백

subscribe_json의 콜백은 `async def`여야 한다. lambda는 코루틴을 반환하지 않으므로
오류가 발생하거나 silent failure가 난다.

```python
# 잘못됨
await subscribe_json(nc, "topic", lambda data: received.append(data))

# 올바름
async def cb(data: dict) -> None:
    received.append(data)
await subscribe_json(nc, "topic", cb)
```

## 3. anyio_mode = "auto" 미설정 시 동작

설정 전: `async def test_*`는 수집은 되지만 실행되지 않거나 coroutine 경고가 남.
해결: pyproject.toml `[tool.pytest.ini_options]`에 `anyio_mode = "auto"` 추가.

## 4. queue group 테스트 타이밍

4개 메시지 발행 후 `anyio.sleep(0.5)` 이상 대기 필요.
0.3초 이하에서는 간헐적으로 메시지 일부 누락 가능.
