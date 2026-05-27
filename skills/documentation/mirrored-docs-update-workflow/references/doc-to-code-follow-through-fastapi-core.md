# Doc-to-Code Follow-Through Pattern (FastAPI core SDK)

## Trigger
- User sequence is: (1) update docs/specs, then (2) "reflect in code and write tests".

## Practical workflow
1. Treat updated docs (`docs/prd.md`, `docs/api.md`, `docs/config.md`) as implementation contract.
2. Implement matching code changes across:
   - config models (new env/YAML fields)
   - core modules (new utility functions)
   - dependencies (new DI providers)
   - routers (behavior/error mapping)
3. Add/adjust tests at both unit and integration levels when available.
4. Run full non-integration suite and report exact pass counts.

## Concrete mappings used
- DB docs -> code:
  - Added DB pool config fields to `DatabaseConfig`
  - `create_db_engine()` forwards pool args
  - Added `run_in_transaction()`
  - Added `get_db_session()` dependency
- Storage docs -> code:
  - Added `MinIOConfig.presigned_expires_sec`
  - Added `generate_presigned_get_url()` / `generate_presigned_put_url()`
- Readiness docs -> code:
  - Added `HealthSettings` under `ServiceSettings`
  - `/health/readiness` checks Keycloak + DB + MinIO with per-check toggles and 503 detail mapping
- NATS messaging docs -> code:
  - Added `NatsConfig` model to `config.py` with `server_list` property (comma-split)
  - Added `EnvConfig.nats: NatsConfig` field
  - Created `fastapi_core/core/messaging.py`: `create_nats_client`, `publish_json`, `subscribe_json`
  - Created `fastapi_core/dependencies/messaging.py`: `set_nats_client` (async), `get_nats_client`
  - Pattern mirrors storage dependency exactly: set with direct client or config, get raises RuntimeError if not initialized

## Test design notes
- Unit tests:
  - Assert new create_engine kwargs for pool settings.
  - Assert transaction helper commit/rollback paths.
  - Assert session dependency closes session.
  - Assert presigned URL helper methods call MinIO client with proper HTTP verb.
  - Assert readiness failure branches for DB/MinIO with expected detail strings.
  - Assert NATS connect called with correct args (servers as list, reconnect_time_wait in seconds not ms).
  - Assert publish_json serializes to UTF-8 bytes.
  - Assert subscribe_json passes internal handler that deserializes JSON before calling cb.
  - Assert set_nats_client raises ValueError when both client and config are None.
  - Assert get_nats_client raises RuntimeError when nats_client not in app.state.

## Async test pattern (IMPORTANT)
- This project does NOT use pytest-asyncio. Use `anyio.run(async_fn)` directly in sync test methods.
- Pattern:
  ```python
  import anyio

  class TestFoo:
      def test_something_async(self):
          mock_client = AsyncMock()
          async def run():
              await some_async_fn(mock_client)
          anyio.run(run)
          mock_client.method.assert_awaited_once()
  ```
- Do NOT use `@pytest.mark.asyncio` — it will silently skip or error without pytest-asyncio installed.
- Integration tests:
  - DB: validate `get_db_session` + `run_in_transaction` with `SELECT 1`.
  - MinIO: validate presigned URL generation returns URL-like strings.

## Outcome verification example
- `uv run pytest -q` result in this session: `93 passed, 4 warnings` (non-integration suite).
