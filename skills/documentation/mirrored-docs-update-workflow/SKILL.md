---
name: mirrored-docs-update-workflow
description: Update product/API/config docs in repositories that keep duplicate documentation trees, then mirror changes and verify consistency.
---

# Mirrored Docs Update Workflow

## When to use
- A repo stores documentation in two locations that must stay identical (e.g., `/docs` and a package-scoped docs directory like `/fastapi_core/docs`).
- User asks to “reflect/add” feature requirements in docs before code implementation.
- You need to update PRD/API/config docs and README together without drifting copies.

## Core approach
1. **Identify canonical edit targets first**
   - Edit the top-level docs set first (commonly `/docs/*.md`) and README if relevant.
   - Explicitly mark roadmap/spec-only additions as planned (e.g., `*(추가 예정)*`) when implementation does not yet exist.

2. **Apply focused doc edits**
   - Update PRD for capability-level requirements.
   - Update API spec for endpoint behavior, error table, and new planned interfaces.
   - Update config guide for new env/YAML keys and sample snippets.
   - Update README summary bullets to keep public overview aligned.

3. **Choose and enforce the source-of-truth layout**
   - **Default (mirrored repos):** copy changed files into mirrored package docs path (e.g., `/fastapi_core/docs/*`).
   - **If user requests single-tree docs:** keep only canonical docs (usually `/docs/*`), remove duplicate tree, and update links/references to canonical paths.

4. **When feature/test scope changed, sync the test guide (`docs/test.md`)**
   - Update the per-file test coverage table so it reflects newly added test modules or expanded scope (e.g., readiness now includes Keycloak+DB+MinIO, storage includes presigned URL tests).
   - Update function-level validation tables for files that gained new tests (add exact test function names and expected assertions/outcomes).
   - Prefer additive section updates over broad rewrites to avoid accidental markdown drift.

5. **Verify before reporting done**
   - Mirrored layout: confirm diff includes both primary docs and mirrored copies.
   - Single-tree layout: confirm duplicate docs directory is removed and README/internal references point to canonical `/docs/*` paths.
   - Check no accidental contradictions (e.g., readiness text in API vs PRD vs README).
   - Ensure “planned” markers are consistent anywhere behavior is not implemented yet.

## Pitfalls
- **Async test framework mismatch**: This project uses `anyio` (not pytest-asyncio). Use `anyio.run(async_fn)` inside sync test methods. `@pytest.mark.asyncio` silently fails without the plugin installed.
- **Ambiguous patch hunks in large markdown files**: broad multi-hunk patching can fail when repeated headings/tables exist. Use narrower unique replacements or stepwise edits.
- **Partial-read overwrite risk**: if file was read in paginated chunks, avoid full overwrite unless you re-read complete content.
- **Spec drift**: updating PRD/API only and forgetting README/config (or mirror path) causes user-visible inconsistency.
- **Test-doc drift after code/test changes**: `docs/test.md` is easy to miss; if tests were added or semantics changed, update both summary tables and detailed test-case sections in the same pass.
- **Layout mode confusion after normalization**: once the user switches to single-tree docs (`/docs/*` only), stop mirroring/copying into package docs paths and only update canonical docs.
- **Doc-first follow-through gap**: when the user immediately asks to implement newly documented features, treat docs as source of truth and update code + tests in one pass (don’t stop at docs).

## Minimal completion checklist
- [ ] PRD updated with requested feature scope
- [ ] API doc updated (behavior + error outcomes)
- [ ] Config doc updated (keys + examples)
- [ ] README summary updated
- [ ] Layout decision applied (mirrored or single-tree per user request)
- [ ] If mirrored: mirrored docs tree synced
- [ ] If single-tree: duplicate docs tree removed
- [ ] References/links updated to canonical docs paths
- [ ] Diff confirms consistency with chosen layout

## References
- `references/fastapi-core-doc-sync-example.md` — concrete example of dual-tree doc updates (readiness + DB/storage enhancements) and wording conventions.
- `references/single-tree-docs-normalization.md` — how to convert duplicated docs layout to canonical `/docs` only and update links safely.
- `references/doc-to-code-follow-through-fastapi-core.md` — pattern for implementing newly documented features immediately in code + tests (config/core/dependencies/routers + verification).
