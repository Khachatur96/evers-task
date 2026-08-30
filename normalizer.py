"""Social Profile Normalizer.

Reduces platform-specific raw API responses (LinkedIn, Instagram, TikTok) to
one consistent `UnifiedProfile`. See CLAUDE_CODE_SPEC.md and NORMALIZER_DESIGN.md
for the full spec and design rationale.
"""

from pydantic import BaseModel


class ProfileFetchError(Exception):
    """Raised when the raw response is an error envelope, not a profile."""


class UnifiedProfile(BaseModel):
    platform: str                      # "linkedin" | "instagram" | "tiktok"
    user_id: str                       # stable platform identifier
    display_name: str | None = None    # best human-readable name
    handle: str | None = None          # username/vanity slug, NO leading @
    bio: str | None = None             # headline or biography; "" becomes None
    avatar_url: str | None = None      # profile picture URL
    follower_count: int | None = None  # None when platform/scope doesn't provide it


def _str_or_none(value: str | None) -> str | None:
    """Return None if value is None or empty/whitespace-only, else the stripped string."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


# ---------------------------------------------------------------------------
# LinkedIn field functions
# ---------------------------------------------------------------------------

def get_linkedin_user_id(raw: dict) -> str:
    return raw["id"]


def get_linkedin_display_name(raw: dict) -> str | None:
    first = _str_or_none(raw.get("localizedFirstName"))
    last = _str_or_none(raw.get("localizedLastName"))
    if first and last:
        return f"{first} {last}"
    return first


def get_linkedin_handle(raw: dict) -> str | None:
    return _str_or_none(raw.get("vanityName"))


def get_linkedin_bio(raw: dict) -> str | None:
    return _str_or_none(raw.get("localizedHeadline"))


def get_linkedin_avatar_url(raw: dict) -> str | None:
    picture = raw.get("profilePicture")
    if not picture:
        return None
    decorated = picture.get("displayImage~")
    if not decorated:
        return None
    elements = decorated.get("elements") or []
    if not elements:
        return None

    def _area(element: dict) -> int:
        size = (
            element.get("data", {})
            .get("com.linkedin.digitalmedia.mediaartifact.StillImage", {})
            .get("storageSize", {})
        )
        return size.get("width", 0) * size.get("height", 0)

    largest = max(elements, key=_area)
    identifiers = largest.get("identifiers") or []
    if not identifiers:
        return None
    return identifiers[0].get("identifier")


def get_linkedin_follower_count(raw: dict) -> int | None:
    return None


# ---------------------------------------------------------------------------
# Instagram field functions
# ---------------------------------------------------------------------------

def get_instagram_user_id(raw: dict) -> str:
    return raw["id"]


def get_instagram_display_name(raw: dict) -> str | None:
    return _str_or_none(raw.get("name"))


def get_instagram_handle(raw: dict) -> str | None:
    return _str_or_none(raw.get("username"))


def get_instagram_bio(raw: dict) -> str | None:
    return _str_or_none(raw.get("biography"))


def get_instagram_avatar_url(raw: dict) -> str | None:
    return _str_or_none(raw.get("profile_picture_url"))


def get_instagram_follower_count(raw: dict) -> int | None:
    return raw.get("followers_count")


# ---------------------------------------------------------------------------
# TikTok field functions
# ---------------------------------------------------------------------------

def get_tiktok_user_id(raw: dict) -> str:
    return raw["data"]["user"]["open_id"]


def get_tiktok_display_name(raw: dict) -> str | None:
    return _str_or_none(raw["data"]["user"].get("display_name"))


def get_tiktok_handle(raw: dict) -> str | None:
    return _str_or_none(raw["data"]["user"].get("username"))


def get_tiktok_bio(raw: dict) -> str | None:
    return _str_or_none(raw["data"]["user"].get("bio_description"))


def get_tiktok_avatar_url(raw: dict) -> str | None:
    return _str_or_none(raw["data"]["user"].get("avatar_url"))


def get_tiktok_follower_count(raw: dict) -> int | None:
    return raw["data"]["user"].get("follower_count")


# ---------------------------------------------------------------------------
# Assembler functions
# ---------------------------------------------------------------------------

def assemble_linkedin(raw: dict) -> UnifiedProfile:
    return UnifiedProfile(
        platform="linkedin",
        user_id=get_linkedin_user_id(raw),
        display_name=get_linkedin_display_name(raw),
        handle=get_linkedin_handle(raw),
        bio=get_linkedin_bio(raw),
        avatar_url=get_linkedin_avatar_url(raw),
        follower_count=get_linkedin_follower_count(raw),
    )


def assemble_instagram(raw: dict) -> UnifiedProfile:
    return UnifiedProfile(
        platform="instagram",
        user_id=get_instagram_user_id(raw),
        display_name=get_instagram_display_name(raw),
        handle=get_instagram_handle(raw),
        bio=get_instagram_bio(raw),
        avatar_url=get_instagram_avatar_url(raw),
        follower_count=get_instagram_follower_count(raw),
    )


def assemble_tiktok(raw: dict) -> UnifiedProfile:
    error = raw.get("error", {})
    if error.get("code") != "ok":
        raise ProfileFetchError(error.get("message", "Unknown TikTok error"))

    return UnifiedProfile(
        platform="tiktok",
        user_id=get_tiktok_user_id(raw),
        display_name=get_tiktok_display_name(raw),
        handle=get_tiktok_handle(raw),
        bio=get_tiktok_bio(raw),
        avatar_url=get_tiktok_avatar_url(raw),
        follower_count=get_tiktok_follower_count(raw),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_ASSEMBLERS = {
    "linkedin": assemble_linkedin,
    "instagram": assemble_instagram,
    "tiktok": assemble_tiktok,
}


def normalize(platform: str, raw: dict) -> UnifiedProfile:
    """Dispatch to the right per-platform assembler and return a UnifiedProfile.
    Raise ValueError on an unknown platform and ProfileFetchError on an error-envelope response."""
    assembler = _ASSEMBLERS.get(platform)
    if assembler is None:
        raise ValueError(f"Unknown platform: {platform!r}")
    return assembler(raw)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from fixtures import ALL_FIXTURES

    for platform, label, payload in ALL_FIXTURES:
        print(f"\n{'='*60}")
        print(f"{platform.upper()} — {label}")
        print(f"{'='*60}")
        try:
            profile = normalize(platform, payload)
            print(profile.model_dump_json(indent=2))
        except ProfileFetchError as e:
            print(f"ProfileFetchError: {e}")

# Where token refresh belongs:
#
# Token refresh is an I/O + auth concern that belongs in the API-calling layer,
# before normalize() is ever invoked — e.g. inside the client wrapper that
# performs the HTTP GET, catches a 401, refreshes the access token, and retries
# the request. It does NOT belong inside these normalization functions because:
#
#   1. Purity: field-extraction functions take a raw dict and return a value,
#      with no I/O and no side effects. A refresh call is network I/O — mixing
#      it in breaks that contract and makes the functions impossible to test
#      with static fixtures alone.
#   2. Separation of concerns: normalize() answers "what does this JSON mean?"
#      A token refresh answers "how do we get valid JSON in the first place?"
#      Those are different layers with different failure modes and different
#      retry/backoff policies.
#   3. Testability: because these functions are pure, the entire test suite
#      here runs against fixtures.py with zero network access. If refresh
#      logic lived inside normalize(), every test would need to mock HTTP
#      calls and token state instead of just asserting on dict -> value.
