"""The crop-name map (F18): Tomato works everywhere, unknown crops answer None."""

import pytest

from app.main import DEFAULT_CROP_TYPES
from app.modules import crops
from app.modules.crop_rescue.core import shelf_life
from app.modules.crops import CROP_RESCUE, FORECASTER, VOICE, component_crop, rescue_code, supported_crops

COMPONENTS = (CROP_RESCUE, FORECASTER, VOICE)


def test_tomato_maps_to_every_component():
    assert component_crop(CROP_RESCUE, "Tomato") == "tomato"
    assert component_crop(FORECASTER, "Tomato") == "Tomato"
    assert component_crop(VOICE, "Tomato") == "tomato"


def test_tomato_is_the_only_crop_every_component_supports():
    everywhere = [
        name for name, mapped in crops.CROP_MAP.items() if all(mapped[c] is not None for c in COMPONENTS)
    ]
    assert everywhere == ["Tomato"]


def test_spinach_is_crop_rescue_only():
    assert component_crop(CROP_RESCUE, "Spinach") == "spinach"
    assert component_crop(FORECASTER, "Spinach") is None
    assert component_crop(VOICE, "Spinach") is None


def test_forecaster_crops_are_exactly_onion_tomato_potato():
    assert sorted(supported_crops(FORECASTER)) == ["Onion", "Potato", "Tomato"]


def test_crop_rescue_supports_the_eight_crops():
    assert sorted(supported_crops(CROP_RESCUE)) == sorted(
        ["Tomato", "Spinach", "Okra", "Brinjal", "Cauliflower", "Grapes", "Capsicum", "Cucumber"]
    )


def test_lookup_ignores_case_and_spaces():
    assert component_crop(CROP_RESCUE, "  tOMATO ") == "tomato"


def test_unknown_crop_or_component_gives_none():
    assert component_crop(CROP_RESCUE, "Dragonfruit") is None
    assert component_crop("no_such_component", "Tomato") is None


def test_every_mapped_crop_is_seeded_in_crop_types():
    seeded = {c["name"] for c in DEFAULT_CROP_TYPES}
    assert set(crops.CROP_MAP) <= seeded


def test_every_map_entry_names_all_components():
    for name, mapped in crops.CROP_MAP.items():
        assert set(mapped) == set(COMPONENTS), name


def test_rescue_code_prefers_researched_then_named_estimate_then_category():
    assert rescue_code("Tomato") == "tomato"
    assert rescue_code(" wheat ", "Cereal") == "wheat"
    assert rescue_code("Dragonfruit", "Fruit") == "est_fruit"
    assert rescue_code("Lentil", "pulse") == "est_grain"
    assert rescue_code("Mystery", None) == "est_other"


def test_every_seeded_crop_gets_a_rescue_code_crop_rescue_knows():
    known = shelf_life.load_crops()
    for crop in DEFAULT_CROP_TYPES:
        assert rescue_code(crop["name"], crop.get("category")) in known, crop["name"]


def test_only_the_eight_researched_crops_are_not_estimates():
    known = shelf_life.load_crops()
    researched = sorted(code for code, crop in known.items() if not crop.estimate)
    assert researched == sorted(
        ["tomato", "spinach", "okra", "brinjal", "cauliflower", "grapes", "capsicum", "cucumber"]
    )
    assert known["wheat"].estimate and known["est_other"].estimate
