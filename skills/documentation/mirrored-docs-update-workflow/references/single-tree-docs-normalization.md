# Single-tree docs normalization (fastapi-core pattern)

## Trigger
User asks to stop maintaining duplicated docs trees and keep only `docs/*`.

## Steps used
1. Identify both trees:
   - Canonical: `/docs/{api,config,prd,test}.md`
   - Duplicate: `/fastapi_core/docs/{api,config,prd,test}.md`
2. Update links in `README.md` from `fastapi_core/docs/...` to `docs/...`.
3. Delete duplicate docs files and remove duplicate directory if empty.
4. Verify:
   - `docs/*` files still present
   - `fastapi_core/docs` no longer exists
   - content search has no live references to `fastapi_core/docs/` in source docs/README

## Notes
- `*.egg-info` may still contain old paths (`SOURCES.txt`, `PKG-INFO`) because they are build artifacts. Treat separately from source docs normalization.
- When user asks for source-tree normalization only, do not overreach into packaging metadata unless requested.
