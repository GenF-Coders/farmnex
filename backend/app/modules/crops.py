"""One place that says which crops each component understands.

Main app crop names (`crop_types.name`, capitalised) map to the name or code each component uses.
`None` means the component does not support that crop yet. Only Tomato is supported everywhere,
so the demo story uses Tomato.

Component code asks `component_crop(component, crop_name)`; if it gets `None`, it should answer
with NOT_AVAILABLE_MESSAGE instead of failing.
"""

from typing import Final

CROP_RESCUE: Final = "crop_rescue"  # lowercase crop_code, from farmnex_crop_rescue crops.json
FORECASTER: Final = "forecaster"  # capitalised, exactly as in the forecaster's config.yaml
VOICE: Final = "voice"  # lowercase voice crop id

NOT_AVAILABLE_MESSAGE: Final = "Not available for this crop yet."

# crop_types.name -> {component: that component's name for the crop, or None}
CROP_MAP: Final[dict[str, dict[str, str | None]]] = {
    "Tomato": {CROP_RESCUE: "tomato", FORECASTER: "Tomato", VOICE: "tomato"},
    "Onion": {CROP_RESCUE: None, FORECASTER: "Onion", VOICE: "onion"},
    "Potato": {CROP_RESCUE: None, FORECASTER: "Potato", VOICE: "potato"},
    # Crop Rescue only. The voice service will also take these once its FARMNEX_HOST change is
    # done; until then they stay None.
    "Spinach": {CROP_RESCUE: "spinach", FORECASTER: None, VOICE: None},
    "Okra": {CROP_RESCUE: "okra", FORECASTER: None, VOICE: None},
    "Brinjal": {CROP_RESCUE: "brinjal", FORECASTER: None, VOICE: None},
    "Cauliflower": {CROP_RESCUE: "cauliflower", FORECASTER: None, VOICE: None},
    "Grapes": {CROP_RESCUE: "grapes", FORECASTER: None, VOICE: None},
    "Capsicum": {CROP_RESCUE: "capsicum", FORECASTER: None, VOICE: None},
    "Cucumber": {CROP_RESCUE: "cucumber", FORECASTER: None, VOICE: None},
    # In crop_types but supported by no component yet.
    "Rice": {CROP_RESCUE: None, FORECASTER: None, VOICE: None},
    "Wheat": {CROP_RESCUE: None, FORECASTER: None, VOICE: None},
    "Maize": {CROP_RESCUE: None, FORECASTER: None, VOICE: None},
    "Cotton": {CROP_RESCUE: None, FORECASTER: None, VOICE: None},
    "Sugarcane": {CROP_RESCUE: None, FORECASTER: None, VOICE: None},
    "Groundnut": {CROP_RESCUE: None, FORECASTER: None, VOICE: None},
    "Mango": {CROP_RESCUE: None, FORECASTER: None, VOICE: None},
    "Banana": {CROP_RESCUE: None, FORECASTER: None, VOICE: None},
    "Carrot": {CROP_RESCUE: None, FORECASTER: None, VOICE: None},
}

_BY_LOWER_NAME: Final = {name.lower(): crops for name, crops in CROP_MAP.items()}


def component_crop(component: str, crop_name: str) -> str | None:
    """The component's own name/code for a main-app crop, or None if it isn't supported.

    `crop_name` is matched ignoring case and surrounding spaces. Unknown crops give None.
    """
    crops = _BY_LOWER_NAME.get(crop_name.strip().lower())
    if crops is None:
        return None
    return crops.get(component)


def supported_crops(component: str) -> list[str]:
    """Main-app crop names (`crop_types.name`) that this component supports."""
    return [name for name, crops in CROP_MAP.items() if crops.get(component) is not None]
