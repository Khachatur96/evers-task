# Social Profile Normalizer — Design & Rationale

This document explains the logic behind `normalizer.py` and why this
architecture is the right fit for the problem described in
`CLAUDE_CODE_SPEC.md`.

## The core problem

Three platforms describe the same concept — "a user's public profile" — with
three incompatible shapes:

| | LinkedIn | Instagram | TikTok |
|---|---|---|---|
| Envelope | flat object | flat object, no envelope | `{data: {user: {...}}, error: {...}}` |
| Name | split first/last, locale-wrapped | single `name` field | single `display_name` field |
| Avatar | paginated sub-document, pick largest | single URL field | single URL field |
| Missing-field signal | key absent | key absent, or `""`, or a boolean flag (`has_profile_pic`) | key absent, or `""` |
| Failure signal | n/a in fixtures | n/a in fixtures | `error.code != "ok"` |

Any single "one big function per platform" implementation would work for the
happy path, but conflating field extraction with error handling and
input-shape quirks tends to produce code where a bug in one field's logic
(e.g. LinkedIn's nested avatar lookup) can silently affect unrelated fields,
and where it's hard to unit test one field in isolation.

## Why this decomposition

**One pure function per field, per platform.** Each `get_<platform>_<field>`
function has a single job: given the raw dict, return the normalized value or
`None`. This is the design the spec calls for, and it pays off in three
concrete ways:

1. **Testability in isolation.** You can assert `get_linkedin_avatar_url(LINKEDIN_SPARSE) is None`
   without touching name/bio/handle logic at all. A bug in avatar extraction
   can't hide behind or interfere with a bug in bio extraction.
2. **Locality of platform quirks.** LinkedIn's "pick the largest image
   resolution" logic, Instagram's "`""` means sparse" logic, and TikTok's
   "fields live under `data.user`" logic each live in exactly one place. A
   reader auditing "how do we get the avatar for LinkedIn" reads one ~15-line
   function, not a 100-line assembler with three platforms interleaved.
3. **No hidden coupling.** Pure functions (no globals, no shared mutable
   state, no I/O) mean the order functions run in, and how many times, never
   matters. This is what makes the fixtures-only test story possible — no
   mocking required anywhere in the extraction layer.

**One assembler per platform.** Each `assemble_<platform>` is a thin
composition layer — it calls its field functions and packs the results into
a `UnifiedProfile`. It has exactly one piece of real logic per platform: for
TikTok, the error-envelope check, which runs *before* any field function is
called. That ordering matters — the spec is explicit that on an error
envelope we must raise, never return a half-empty profile, so the check has
to gate field extraction rather than run alongside it.

**One dispatcher (`normalize`).** A single `dict`-based dispatch table maps
platform name to assembler. This keeps the "which platform is this" decision
in exactly one place, and makes adding a fourth platform a two-line change
(one field-function set + assembler, one dict entry) rather than a change to
branching logic scattered across the module.

## Why `None` vs `""` vs `0` are handled the way they are

The spec's hardest judgment call is distinguishing three states that a naive
implementation collapses into one "falsy" bucket:

- **Absent key** → the platform/scope never sent this field at all (e.g.
  TikTok `follower_count` under a basic-only token). This is "unknown."
- **Empty string** → the platform sent the field, and explicitly said there's
  nothing there (e.g. Instagram `biography: ""` on a fresh account). This is
  "known to be nothing," and per the spec should also normalize to `None`,
  because a consumer of `UnifiedProfile` shouldn't have to special-case `""`
  vs `None` — they mean the same thing to anyone downstream.
- **Genuine `0`** → the platform sent real data, and the value happens to be
  zero (e.g. Instagram sparse `followers_count: 0` — a real, freshly-created
  account with zero followers). This must **not** collapse to `None`, because
  `None` means "we don't know," while `0` means "we know, and it's zero."

This is why `_str_or_none` exists as a single shared helper instead of being
duplicated per field: it exactly implements the "absent-or-empty → None,
otherwise stripped string" rule for every string field on every platform, so
that rule is defined once and can't drift between platforms. Numeric fields
(`follower_count`) deliberately do **not** go through this helper — they use
plain `raw.get(...)`, which returns `None` on a missing key and passes real
integers (including `0`) straight through untouched. Using one shared
string-emptiness rule and one shared missing-key rule, rather than ad hoc
per-field conditionals, is what keeps "unknown / empty / zero" consistently
distinguished across 15+ field functions instead of relying on every
function author getting it right independently.

## Why the LinkedIn avatar picks "largest by area"

LinkedIn's `displayImage~.elements` is a list of the same image at multiple
resolutions (100×100, 400×400, ...). The spec calls for "the largest
resolution element." Rather than assuming a fixed ordering or a known set of
sizes (fragile — the API could reorder elements or add a new size tier), the
extraction computes `width * height` from each element's
`storageSize` and takes the max. This is the one field function with any
real control flow, which is exactly why it's isolated in its own function
with early returns for the two "not available" cases (`profilePicture`
absent, `displayImage~` absent) before doing any list work.

## Why the TikTok error check lives in the assembler, not `normalize`

The error envelope (`error.code`) is a property of the TikTok response shape
specifically — Instagram and LinkedIn fixtures have no equivalent envelope at
all. Putting the check in the shared `normalize()` dispatcher would mean
special-casing one platform's shape inside the platform-agnostic dispatch
logic. Keeping it inside `assemble_tiktok` keeps `normalize()` truly generic
(just a lookup + call) and keeps all TikTok-specific knowledge, including its
failure mode, inside the TikTok assembler where a reader would expect to find
it.

## Why token refresh doesn't belong here

Token refresh is I/O plus auth state management: it requires making a network
call, handling retry/backoff, and persisting the new token somewhere. The
field-extraction and assembler functions in this module are pure — dict in,
value out — which is precisely what makes them testable against static
fixtures with zero mocking. Folding refresh logic in would mean:

- Every field/assembler function could now fail for reasons unrelated to the
  shape of `raw` (network errors, expired refresh tokens), breaking the
  "never crash on the fields that aren't there" contract in a new way.
- Tests would need to mock HTTP and token state instead of asserting on plain
  dicts.

Token refresh belongs in the API-calling layer, one level up: the code that
performs `GET /v2/me` (or the Instagram/TikTok equivalent), catches a 401,
refreshes the token, and retries — handing `normalize()` a raw dict only once
a valid response has actually been obtained.

## Result

Running `python3 normalizer.py` produces 6 successful `UnifiedProfile` JSON
dumps and 1 `ProfileFetchError`, matching the "Expected Output Summary" table
in `CLAUDE_CODE_SPEC.md` field-for-field, with zero crashes on either the OK
or sparse fixtures.
