---
name: onsite-coding-standards
description: Engineering and coding best practices for Onsite — TypeScript, React, Next.js, Python, testing, APIs. Use when writing or reviewing code in Onsite repos.
---

# Onsite Coding Standards

## TypeScript / React / Next.js

- Prefer **functional components** and **hooks**. No class components unless legacy.
- **Type everything:** Avoid `any`. Use interfaces for API responses and props.
- **Error handling:** Log and rethrow with cause. No empty catch.
- **Async:** Prefer async/await. Handle loading and error states in UI.
- **Files:** One main component per file. Colocate styles or use Tailwind. Paths: `@/` for src if configured.

```typescript
// Good: typed, explicit error
try {
  const data = await fetchData();
  return data;
} catch (e) {
  logger.error('Fetch failed', { error: e });
  throw new DataFetchError('Unable to load', { cause: e });
}
```

---

## Python (FastAPI / scripts)

- **Type hints** on function args and return. Use Pydantic for request/response.
- **Env:** Never commit secrets. Use env vars or secret manager.
- **Imports:** Standard library first, then third-party, then local. Format with isort/black.
- **Errors:** Raise specific exceptions; log before raise where useful.

```python
def parse_revenue(val: str | None) -> float:
    if not val: return 0.0
    cleaned = val.replace("Rs.", "").replace("₹", "").replace(",", "").strip()
    try: return float(cleaned)
    except ValueError: return 0.0
```

---

## APIs & Data

- **REST:** Consistent naming (kebab or snake). Version if public. Use appropriate status codes.
- **CSV:** Use UTF-8 with BOM for Excel compatibility when needed. Validate headers and required columns before processing.
- **Dates:** Store UTC; convert to local for display. Use same parsing pattern across analytics (see onsite-data-analytics).

---

## Testing

- **Unit:** Critical business logic (revenue parsing, date parsing, serial number rules). Mock I/O.
- **Naming:** `test_<what>_<expected>` (e.g. `test_parse_revenue_with_rs_prefix_returns_float`).
- **Data:** Use small, realistic fixtures. No production data in repo.

---

## Security & Config

- No hardcoded API keys or passwords. Use env and .env.example (no secrets in example).
- Validate and sanitize user input for uploads (BOQ, CSVs). Limit file size and row count where applicable.
