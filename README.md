# Social Profile Normalizer

Onboarding exercise. Takes raw API responses from LinkedIn, Instagram, and TikTok and reduces them to a single consistent `UnifiedProfile`.

## Setup

```bash
pip install pydantic pytest
```

## Run

```bash
python normalizer.py
```

Prints 6 normalized profiles and 1 `ProfileFetchError` (TikTok revoked token).

## Test

```bash
pytest test_normalizer.py -v
```

51 tests covering field extraction, sparse/absent fields, `""` vs `None` vs `0` edge cases, and the error-envelope path.

## Files

| File | Purpose |
|---|---|
| `normalizer.py` | Normalization logic — the deliverable |
| `fixtures.py` | Fake-but-realistic API responses (do not edit) |
| `test_normalizer.py` | pytest test suite |
| `NORMALIZER_DESIGN.md` | Design decisions and rationale behind the implementation |