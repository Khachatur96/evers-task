"""Tests for normalizer.py.

Covers: the OK/sparse/error fixtures end-to-end, plus the specific judgment
calls the spec cares about most — "" vs None vs 0, absent keys, the
error-envelope path, and the LinkedIn largest-avatar selection.
"""

import pytest

from fixtures import (
    INSTAGRAM_OK,
    INSTAGRAM_SPARSE,
    LINKEDIN_OK,
    LINKEDIN_SPARSE,
    TIKTOK_ERROR,
    TIKTOK_OK,
    TIKTOK_SPARSE,
)
from normalizer import (
    ProfileFetchError,
    UnifiedProfile,
    _str_or_none,
    get_instagram_avatar_url,
    get_instagram_bio,
    get_instagram_display_name,
    get_instagram_follower_count,
    get_instagram_handle,
    get_linkedin_avatar_url,
    get_linkedin_bio,
    get_linkedin_display_name,
    get_linkedin_follower_count,
    get_linkedin_handle,
    get_tiktok_avatar_url,
    get_tiktok_bio,
    get_tiktok_display_name,
    get_tiktok_follower_count,
    get_tiktok_handle,
    normalize,
)


# ---------------------------------------------------------------------------
# _str_or_none helper
# ---------------------------------------------------------------------------

class TestStrOrNone:
    def test_none_stays_none(self):
        assert _str_or_none(None) is None

    def test_empty_string_becomes_none(self):
        assert _str_or_none("") is None

    def test_whitespace_only_becomes_none(self):
        assert _str_or_none("   ") is None

    def test_real_value_is_stripped(self):
        assert _str_or_none("  hello  ") == "hello"

    def test_real_value_unchanged(self):
        assert _str_or_none("hello") == "hello"


# ---------------------------------------------------------------------------
# LinkedIn field functions
# ---------------------------------------------------------------------------

class TestLinkedInFields:
    def test_user_id_ok(self):
        assert get_linkedin_display_name(LINKEDIN_OK) == "Marek Halbrun"

    def test_display_name_combines_first_and_last(self):
        assert get_linkedin_display_name(LINKEDIN_OK) == "Marek Halbrun"

    def test_display_name_falls_back_to_first_only_when_last_is_empty(self):
        # LINKEDIN_SPARSE has localizedLastName == ""
        assert get_linkedin_display_name(LINKEDIN_SPARSE) == "Yusuf"

    def test_display_name_none_when_both_empty(self):
        raw = {"localizedFirstName": "", "localizedLastName": ""}
        assert get_linkedin_display_name(raw) is None

    def test_display_name_none_when_both_absent(self):
        assert get_linkedin_display_name({}) is None

    def test_handle_present(self):
        assert get_linkedin_handle(LINKEDIN_OK) == "marek-halbrun"

    def test_handle_none_when_absent(self):
        assert get_linkedin_handle(LINKEDIN_SPARSE) is None

    def test_bio_present(self):
        assert get_linkedin_bio(LINKEDIN_OK) == "Staff Engineer at Northwind"

    def test_bio_none_when_absent(self):
        assert get_linkedin_bio(LINKEDIN_SPARSE) is None

    def test_avatar_picks_largest_resolution(self):
        url = get_linkedin_avatar_url(LINKEDIN_OK)
        assert url is not None
        assert "shrink_400_400" in url  # not the 100x100 element

    def test_avatar_none_when_no_decorated_expansion(self):
        # LINKEDIN_SPARSE has displayImage but no "displayImage~" expansion
        assert get_linkedin_avatar_url(LINKEDIN_SPARSE) is None

    def test_avatar_none_when_profile_picture_absent(self):
        assert get_linkedin_avatar_url({}) is None

    def test_avatar_none_when_elements_empty(self):
        raw = {"profilePicture": {"displayImage~": {"elements": []}}}
        assert get_linkedin_avatar_url(raw) is None

    def test_follower_count_always_none(self):
        assert get_linkedin_follower_count(LINKEDIN_OK) is None
        assert get_linkedin_follower_count(LINKEDIN_SPARSE) is None


# ---------------------------------------------------------------------------
# Instagram field functions
# ---------------------------------------------------------------------------

class TestInstagramFields:
    def test_display_name_present(self):
        assert get_instagram_display_name(INSTAGRAM_OK) == "Dana Okafor"

    def test_display_name_none_when_absent(self):
        # INSTAGRAM_SPARSE has no "name" key at all
        assert get_instagram_display_name(INSTAGRAM_SPARSE) is None

    def test_handle_present(self):
        assert get_instagram_handle(INSTAGRAM_OK) == "dana.builds"
        assert get_instagram_handle(INSTAGRAM_SPARSE) == "n.vasquez"

    def test_bio_present(self):
        assert get_instagram_bio(INSTAGRAM_OK) == "backend @ northwind"

    def test_bio_empty_string_becomes_none(self):
        assert get_instagram_bio(INSTAGRAM_SPARSE) is None

    def test_avatar_present(self):
        assert get_instagram_avatar_url(INSTAGRAM_OK) is not None

    def test_avatar_none_when_absent(self):
        # INSTAGRAM_SPARSE has has_profile_pic: False, no URL field at all
        assert get_instagram_avatar_url(INSTAGRAM_SPARSE) is None

    def test_follower_count_present(self):
        assert get_instagram_follower_count(INSTAGRAM_OK) == 4820

    def test_follower_count_genuine_zero_is_not_none(self):
        # This is the "0 stays 0" judgment call from the spec.
        result = get_instagram_follower_count(INSTAGRAM_SPARSE)
        assert result == 0
        assert result is not None

    def test_follower_count_none_when_absent(self):
        assert get_instagram_follower_count({}) is None


# ---------------------------------------------------------------------------
# TikTok field functions
# ---------------------------------------------------------------------------

class TestTikTokFields:
    def test_display_name_present(self):
        assert get_tiktok_display_name(TIKTOK_OK) == "Priya Raghunathan"
        assert get_tiktok_display_name(TIKTOK_SPARSE) == "kb"

    def test_handle_present_ok_absent_sparse(self):
        assert get_tiktok_handle(TIKTOK_OK) == "priyarghn"
        assert get_tiktok_handle(TIKTOK_SPARSE) is None

    def test_bio_present_ok_absent_sparse(self):
        assert get_tiktok_bio(TIKTOK_OK) == "sound design, three cats"
        assert get_tiktok_bio(TIKTOK_SPARSE) is None

    def test_avatar_present_ok(self):
        assert get_tiktok_avatar_url(TIKTOK_OK) is not None

    def test_avatar_empty_string_becomes_none_sparse(self):
        # TIKTOK_SPARSE has avatar_url: ""
        assert get_tiktok_avatar_url(TIKTOK_SPARSE) is None

    def test_follower_count_present_ok(self):
        assert get_tiktok_follower_count(TIKTOK_OK) == 128400

    def test_follower_count_none_when_absent_sparse(self):
        # Key is fully absent (basic scope only) -> None, not 0.
        assert get_tiktok_follower_count(TIKTOK_SPARSE) is None


# ---------------------------------------------------------------------------
# normalize() end-to-end, against every fixture
# ---------------------------------------------------------------------------

class TestNormalizeEndToEnd:
    def test_linkedin_ok(self):
        profile = normalize("linkedin", LINKEDIN_OK)
        assert profile.platform == "linkedin"
        assert profile.user_id == "yrZCpj2ZYQ"
        assert profile.display_name == "Marek Halbrun"
        assert profile.handle == "marek-halbrun"
        assert profile.bio == "Staff Engineer at Northwind"
        assert profile.follower_count is None
        assert "shrink_400_400" in profile.avatar_url

    def test_linkedin_sparse(self):
        profile = normalize("linkedin", LINKEDIN_SPARSE)
        assert profile == UnifiedProfile(
            platform="linkedin",
            user_id="8fQmv1LtPa",
            display_name="Yusuf",
            handle=None,
            bio=None,
            avatar_url=None,
            follower_count=None,
        )

    def test_instagram_ok(self):
        profile = normalize("instagram", INSTAGRAM_OK)
        assert profile.platform == "instagram"
        assert profile.user_id == "17841400000000000"
        assert profile.display_name == "Dana Okafor"
        assert profile.handle == "dana.builds"
        assert profile.bio == "backend @ northwind"
        assert profile.avatar_url is not None
        assert profile.follower_count == 4820

    def test_instagram_sparse(self):
        profile = normalize("instagram", INSTAGRAM_SPARSE)
        assert profile == UnifiedProfile(
            platform="instagram",
            user_id="17841400000000001",
            display_name=None,
            handle="n.vasquez",
            bio=None,
            avatar_url=None,
            follower_count=0,
        )

    def test_tiktok_ok(self):
        profile = normalize("tiktok", TIKTOK_OK)
        assert profile.platform == "tiktok"
        assert profile.user_id == "723f24d7-e717-40f8-a2b6-cb8464cd23b4"
        assert profile.display_name == "Priya Raghunathan"
        assert profile.handle == "priyarghn"
        assert profile.bio == "sound design, three cats"
        assert profile.avatar_url is not None
        assert profile.follower_count == 128400

    def test_tiktok_sparse(self):
        profile = normalize("tiktok", TIKTOK_SPARSE)
        assert profile == UnifiedProfile(
            platform="tiktok",
            user_id="1d9a5e60-4c2b-4f3e-9a77-0b6d51e2c8aa",
            display_name="kb",
            handle=None,
            bio=None,
            avatar_url=None,
            follower_count=None,
        )

    def test_tiktok_error_raises(self):
        with pytest.raises(ProfileFetchError):
            normalize("tiktok", TIKTOK_ERROR)

    def test_tiktok_error_message_is_surfaced(self):
        with pytest.raises(ProfileFetchError, match="Access token is invalid"):
            normalize("tiktok", TIKTOK_ERROR)

    def test_unknown_platform_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown platform"):
            normalize("facebook", {})

    @pytest.mark.parametrize("platform,payload", [
        ("linkedin", LINKEDIN_OK),
        ("linkedin", LINKEDIN_SPARSE),
        ("instagram", INSTAGRAM_OK),
        ("instagram", INSTAGRAM_SPARSE),
        ("tiktok", TIKTOK_OK),
        ("tiktok", TIKTOK_SPARSE),
    ])
    def test_all_success_fixtures_return_unified_profile(
        self, platform, payload
    ):
        profile = normalize(platform, payload)
        assert isinstance(profile, UnifiedProfile)
        assert profile.platform == platform
        assert isinstance(profile.user_id, str) and profile.user_id
