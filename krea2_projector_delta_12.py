import os
import json
import torch
import comfy.sd

TARGET_KEY = "diffusion_model.txtfusion.projector.weight"
PRESET_FILE = "presets.json"


def _preset_path():
    return os.path.join(os.path.dirname(__file__), PRESET_FILE)


def _load_presets():
    path = _preset_path()
    if not os.path.exists(path):
        return {
            "FB2": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.51171875, -0.890625, 0.0, 0.0],
            "FB3": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.51171875, -0.890625, -0.609375, 0.0],
            "FEDOR": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.5116999745368958, -0.8906000256538391, 0.0, 0.0],
            "SKC3VO": [-0.054443359375, -0.1611328125, 0.37109375, 0.50390625, 0.70703125, 0.39453125, 0.3984375, -1.4375, -0.51171875, -0.890625, -0.609375, 0.11279296875],
        }

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    presets = {}
    for name, item in raw.items():
        values = item["values"] if isinstance(item, dict) else item
        if not isinstance(values, list) or len(values) != 12:
            raise ValueError(f"Preset '{name}' must contain exactly 12 values.")
        presets[name] = [float(v) for v in values]
    return presets


def _format_values(values):
    return ",".join(f"{float(v):.10g}" for v in values)


def _make_delta_tensor(values):
    return torch.tensor([values], dtype=torch.float32)


class Krea2ProjectorDelta12:
    @classmethod
    def INPUT_TYPES(cls):
        presets = _load_presets()
        preset_names = list(presets.keys()) if presets else ["FB2"]

        float_cfg = {
            "default": 0.0,
            "min": -1000.0,
            "max": 1000.0,
            "step": 0.0001,
            "round": False,
        }

        return {
            "required": {
                "model": ("MODEL",),
                "preset": (preset_names, {"default": preset_names[0]}),
                "use_custom": ("BOOLEAN", {"default": False}),
                "strength": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": -100.0,
                        "max": 100.0,
                        "step": 0.01,
                        "round": False,
                    },
                ),
                "d1": ("FLOAT", dict(float_cfg)),
                "d2": ("FLOAT", dict(float_cfg)),
                "d3": ("FLOAT", dict(float_cfg)),
                "d4": ("FLOAT", dict(float_cfg)),
                "d5": ("FLOAT", dict(float_cfg)),
                "d6": ("FLOAT", dict(float_cfg)),
                "d7": ("FLOAT", dict(float_cfg)),
                "d8": ("FLOAT", dict(float_cfg)),
                "d9": ("FLOAT", dict(float_cfg)),
                "d10": ("FLOAT", dict(float_cfg)),
                "d11": ("FLOAT", dict(float_cfg)),
                "d12": ("FLOAT", dict(float_cfg)),
            }
        }

    RETURN_TYPES = (
        "MODEL", "STRING", "STRING",
    )

    RETURN_NAMES = (
        "model", "delta_text", "preset_name",
    )

    FUNCTION = "apply"
    CATEGORY = "model_patches/Krea2"
    DESCRIPTION = "12-slot projector delta editor and patch node for Krea 2."

    def _resolve_base_values(self, preset, use_custom, manual_values):
        if use_custom:
            return [float(v) for v in manual_values]

        presets = _load_presets()
        if preset not in presets:
            raise ValueError(f"Unknown preset: {preset}")

        return list(presets[preset])

    def apply(
        self, model, preset, use_custom, strength,
        d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12
    ):
        manual_values = [d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12]
        base_values = self._resolve_base_values(preset, use_custom, manual_values)
        final_values = [float(v) * float(strength) for v in base_values]

        delta = _make_delta_tensor(final_values)

        m = model.clone()
        patch_dict = {TARGET_KEY: (delta,)}
        m.add_patches(patch_dict, strength_patch=1.0, strength_model=1.0)

        delta_text = _format_values(final_values)
        preset_name = "custom" if use_custom else str(preset)
        strength_value = float(strength)

        return (m, delta_text, preset_name, strength_value, *final_values)


NODE_CLASS_MAPPINGS = {
    "Krea2 Projector Delta 12": Krea2ProjectorDelta12,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Krea2 Projector Delta 12": "Krea2 Projector Delta Advance",
}