"""F1 fast path: the 9 unused modules are not reachable, the rest still are. No database needed."""

from __future__ import annotations

import pytest

UNMOUNTED_PREFIXES = [
    "/api/v2/ai-predictions",
    "/api/v2/ai-recommendations",
    "/api/v2/deliverys",
    "/api/v2/delivery-tracking-events",
    "/api/v2/delivery-proofs",
    "/api/v2/audit-logs",
    "/api/v2/order-disputes",
    "/api/v2/reviews",
    "/api/v2/farm-crop-activitys",
]

STILL_MOUNTED_PREFIXES = [
    "/api/v2/farm-crops",
    "/api/v2/crop-types",
    "/api/v2/product-listings",
    "/api/v2/orders",
    "/api/v2/payments",
    "/api/v2/bids",
]


@pytest.fixture(scope="module")
def openapi_paths() -> list[str]:
    from app.main import app

    return list(app.openapi()["paths"])


@pytest.mark.parametrize("prefix", UNMOUNTED_PREFIXES)
def test_unmounted_module_is_not_in_docs(openapi_paths: list[str], prefix: str) -> None:
    assert not [path for path in openapi_paths if path.startswith(prefix)]


@pytest.mark.parametrize("prefix", STILL_MOUNTED_PREFIXES)
def test_other_modules_are_still_in_docs(openapi_paths: list[str], prefix: str) -> None:
    assert [path for path in openapi_paths if path.startswith(prefix)]
