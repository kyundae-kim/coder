# FastAPI-core dual docs sync example (session note)

## Context
User requested doc-only reflection of planned features from proposal items:
- readiness checks include DB + MinIO (in addition to Keycloak)
- DB convenience enhancements
- storage convenience enhancements

## Effective update pattern
1. Update primary docs under `/docs` first:
   - `docs/prd.md`
   - `docs/api.md`
   - `docs/config.md`
   - `README.md`
2. Mark not-yet-implemented capabilities as `*(추가 예정)*` in API/config/README where needed.
3. Mirror the docs set to package docs:
   - `/fastapi_core/docs/prd.md`
   - `/fastapi_core/docs/api.md`
   - `/fastapi_core/docs/config.md`
4. Verify with diff that both trees changed consistently.

## Content conventions used
- **PRD**: requirement bullets (capability-level)
- **API**: endpoint behavior table + error matrix updates
- **Config**: env key table + `.env` sample additions
- **README**: concise feature bullets only

## Editing pitfalls observed
- Large multi-hunk markdown patch can fail due to repeated headings/tables; prefer smaller unique replacements.
- Avoid full-file overwrite when source was only partially read via offset/limit.

## Example additions captured
- DB planned keys: `DB__POOL_SIZE`, `DB__MAX_OVERFLOW`, `DB__POOL_TIMEOUT`, `DB__POOL_RECYCLE`
- MinIO planned keys: `MINIO__PRESIGNED_EXPIRES_SEC`, `MINIO__ENABLE_VERSIONING`
- readiness API planned failures: `Database not ready`, `MinIO not ready`
