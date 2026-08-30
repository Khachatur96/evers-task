"""Fake-but-realistic API responses for the Social Profile Normalizer exercise.

Nothing here was fetched from a live service and no real person is described.
The *shapes* are real: field names, nesting, envelopes and scope gaps follow the
published contracts of each platform, so code written against these fixtures is
code that would survive the real response.

    LinkedIn    GET https://api.linkedin.com/v2/me
                ?projection=(id,localizedFirstName,localizedLastName,vanityName,
                             localizedHeadline,profilePicture(displayImage~:playableStreams))
    Instagram   GET https://graph.facebook.com/v25.0/{ig-user-id}
                ?fields=id,username,name,biography,profile_picture_url,
                        followers_count,follows_count,media_count,website
    TikTok      GET https://open.tiktokapis.com/v2/user/info/?fields=...

Two properties are worth knowing before you read them, because they are
properties of the platforms rather than of this file:

* The three APIs disagree about what a *response* is. Instagram returns the
  requested fields at the top level with no envelope at all. TikTok wraps
  everything in ``data.user`` and attaches a separate ``error`` object.
  LinkedIn returns a flat object whose picture field expands into a paginated
  sub-document.
* A token does not always carry every scope. TikTok splits its user fields
  across ``user.info.basic`` / ``user.info.profile`` / ``user.info.stats``, and
  LinkedIn's ``r_liteprofile`` returns name and photo where ``r_basicprofile``
  also returns the headline and the vanity name. The sparse fixtures below are
  narrower tokens, not broken ones — the call succeeded.

Seven fixtures: an OK user and a sparse user for each platform, plus TikTok's
error envelope. ``ALL_FIXTURES`` at the bottom lists them in demo order.
"""

# ---------------------------------------------------------------------------
# LinkedIn
# ---------------------------------------------------------------------------

# r_basicprofile, with the profile picture decorated.
#
# `firstName` / `lastName` / `headline` are MultiLocaleStrings: a locale-keyed
# map plus the member's preferred locale. Each also has a flat `localized*`
# twin at the top level, which is the same value already resolved.
LINKEDIN_OK = {
    "id": "yrZCpj2ZYQ",
    "firstName": {
        "localized": {"en_US": "Marek"},
        "preferredLocale": {"country": "US", "language": "en"},
    },
    "localizedFirstName": "Marek",
    "lastName": {
        "localized": {"en_US": "Halbrun"},
        "preferredLocale": {"country": "US", "language": "en"},
    },
    "localizedLastName": "Halbrun",
    "headline": {
        "localized": {"en_US": "Staff Engineer at Northwind"},
        "preferredLocale": {"country": "US", "language": "en"},
    },
    "localizedHeadline": "Staff Engineer at Northwind",
    "vanityName": "marek-halbrun",
    "profilePicture": {
        "displayImage": "urn:li:digitalmediaAsset:C4D03AQGsitRwG8U8ZQ",
        "displayImage~": {
            "paging": {"count": 10, "start": 0, "links": []},
            "elements": [
                {
                    "artifact": (
                        "urn:li:digitalmediaMediaArtifact:"
                        "(urn:li:digitalmediaAsset:C4D03AQGsitRwG8U8ZQ,"
                        "urn:li:digitalmediaMediaArtifactClass:"
                        "profile-displayphoto-shrink_100_100)"
                    ),
                    "authorizationMethod": "PUBLIC",
                    "data": {
                        "com.linkedin.digitalmedia.mediaartifact.StillImage": {
                            "storageSize": {"width": 100, "height": 100},
                            "displaySize": {"uom": "PX", "width": 100, "height": 100},
                            "mediaType": "image/jpeg",
                            "rawCodecSpec": {"name": "jpeg", "type": "image"},
                        }
                    },
                    "identifiers": [
                        {
                            "identifier": (
                                "https://media.licdn.com/dms/image/C4D03AQGsitRwG8U8ZQ/"
                                "profile-displayphoto-shrink_100_100/0?e=1790000000&v=beta"
                            ),
                            "file": (
                                "urn:li:digitalmediaFile:"
                                "(urn:li:digitalmediaAsset:C4D03AQGsitRwG8U8ZQ,"
                                "urn:li:digitalmediaMediaArtifactClass:"
                                "profile-displayphoto-shrink_100_100,0)"
                            ),
                            "index": 0,
                            "mediaType": "image/jpeg",
                            "identifierExpiresInSeconds": 1790000000,
                        }
                    ],
                },
                {
                    "artifact": (
                        "urn:li:digitalmediaMediaArtifact:"
                        "(urn:li:digitalmediaAsset:C4D03AQGsitRwG8U8ZQ,"
                        "urn:li:digitalmediaMediaArtifactClass:"
                        "profile-displayphoto-shrink_400_400)"
                    ),
                    "authorizationMethod": "PUBLIC",
                    "data": {
                        "com.linkedin.digitalmedia.mediaartifact.StillImage": {
                            "storageSize": {"width": 400, "height": 400},
                            "displaySize": {"uom": "PX", "width": 400, "height": 400},
                            "mediaType": "image/jpeg",
                            "rawCodecSpec": {"name": "jpeg", "type": "image"},
                        }
                    },
                    "identifiers": [
                        {
                            "identifier": (
                                "https://media.licdn.com/dms/image/C4D03AQGsitRwG8U8ZQ/"
                                "profile-displayphoto-shrink_400_400/0?e=1790000000&v=beta"
                            ),
                            "file": (
                                "urn:li:digitalmediaFile:"
                                "(urn:li:digitalmediaAsset:C4D03AQGsitRwG8U8ZQ,"
                                "urn:li:digitalmediaMediaArtifactClass:"
                                "profile-displayphoto-shrink_400_400,0)"
                            ),
                            "index": 0,
                            "mediaType": "image/jpeg",
                            "identifierExpiresInSeconds": 1790000000,
                        }
                    ],
                },
            ],
        },
    },
}

# r_liteprofile only: name and photo. No headline and no vanity name are
# returned at this scope. The member also uses a single name and has never
# uploaded a picture, so the asset reference stands alone with nothing
# decorating it.
LINKEDIN_SPARSE = {
    "id": "8fQmv1LtPa",
    "firstName": {
        "localized": {"en_US": "Yusuf"},
        "preferredLocale": {"country": "TR", "language": "tr"},
    },
    "localizedFirstName": "Yusuf",
    "lastName": {
        "localized": {"en_US": ""},
        "preferredLocale": {"country": "TR", "language": "tr"},
    },
    "localizedLastName": "",
    "profilePicture": {
        "displayImage": "urn:li:digitalmediaAsset:C4E03AQHm2ZzTb1kQxw"
    },
}


# ---------------------------------------------------------------------------
# Instagram
# ---------------------------------------------------------------------------

# A Business/Creator account, every requested field granted. Graph API returns
# the fields at the top level; there is no wrapper object on a node read.
INSTAGRAM_OK = {
    "id": "17841400000000000",
    "username": "dana.builds",
    "name": "Dana Okafor",
    "biography": "backend @ northwind",
    "profile_picture_url": (
        "https://scontent.cdninstagram.com/v/t51.2885-19/dana_ig.jpg"
        "?_nc_ht=scontent.cdninstagram.com&oh=00a1b2c3&oe=690F1234"
    ),
    "followers_count": 4820,
    "follows_count": 391,
    "media_count": 68,
    "website": "https://dana.example.dev",
}

# An account opened four days ago and set to private. Every field here was
# granted and returned; the account simply has not been filled in yet.
INSTAGRAM_SPARSE = {
    "id": "17841400000000001",
    "username": "n.vasquez",
    "biography": "",
    "has_profile_pic": False,
    "followers_count": 0,
    "follows_count": 7,
    "media_count": 0,
}


# ---------------------------------------------------------------------------
# TikTok
# ---------------------------------------------------------------------------

# user.info.basic + user.info.profile + user.info.stats.
#
# Note the envelope: `error` is part of every response TikTok sends, including
# this one. On a successful call it carries code "ok" and an empty message.
TIKTOK_OK = {
    "data": {
        "user": {
            "open_id": "723f24d7-e717-40f8-a2b6-cb8464cd23b4",
            "union_id": "c9c60f44-a68e-4f5d-84dd-ce22faeb0ba1",
            "avatar_url": (
                "https://p19-sign.tiktokcdn-us.com/tos-avt-0068-tx/"
                "b17f0e4b3a4f4a50993cf72cda8b88b8~c5_168x168.jpeg"
            ),
            "avatar_url_100": (
                "https://p19-sign.tiktokcdn-us.com/tos-avt-0068-tx/"
                "b17f0e4b3a4f4a50993cf72cda8b88b8~c5_100x100.jpeg"
            ),
            "avatar_large_url": (
                "https://p19-sign.tiktokcdn-us.com/tos-avt-0068-tx/"
                "b17f0e4b3a4f4a50993cf72cda8b88b8~c5_1080x1080.jpeg"
            ),
            "display_name": "Priya Raghunathan",
            "username": "priyarghn",
            "bio_description": "sound design, three cats",
            "profile_deep_link": "https://www.tiktok.com/@priyarghn?_d=secUid",
            "is_verified": False,
            "follower_count": 128400,
            "following_count": 312,
            "likes_count": 2107553,
            "video_count": 194,
        }
    },
    "error": {
        "code": "ok",
        "message": "",
        "log_id": "20260826094402A1B2C3D4E5F60718293A",
    },
}

# The same endpoint, called with a token that carries user.info.basic alone.
# The profile and stats fields are not present — not null, not zero, absent —
# because this token was never authorized for them. The member has no picture.
TIKTOK_SPARSE = {
    "data": {
        "user": {
            "open_id": "1d9a5e60-4c2b-4f3e-9a77-0b6d51e2c8aa",
            "union_id": "5b31c0f2-7ad4-4e19-bb60-2f8c94a17d33",
            "avatar_url": "",
            "display_name": "kb",
        }
    },
    "error": {
        "code": "ok",
        "message": "",
        "log_id": "20260826094511B2C3D4E5F60718293A4B",
    },
}

# The member disconnected the integration from inside the TikTok app, so the
# stored access token no longer resolves. HTTP status was 401.
TIKTOK_ERROR = {
    "data": {},
    "error": {
        "code": "access_token_invalid",
        "message": "Access token is invalid, please refresh token and retry",
        "log_id": "20260826094633C3D4E5F60718293A4B5C",
    },
}


# ---------------------------------------------------------------------------
# (platform, label, payload) — the order the deliverable should demonstrate.
# ---------------------------------------------------------------------------

ALL_FIXTURES = [
    ("linkedin", "ok", LINKEDIN_OK),
    ("linkedin", "sparse", LINKEDIN_SPARSE),
    ("instagram", "ok", INSTAGRAM_OK),
    ("instagram", "sparse", INSTAGRAM_SPARSE),
    ("tiktok", "ok", TIKTOK_OK),
    ("tiktok", "sparse", TIKTOK_SPARSE),
    ("tiktok", "error", TIKTOK_ERROR),
]
