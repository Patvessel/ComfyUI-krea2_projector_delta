import os
import json
import torch
import comfy.sd
from aiohttp import web
from server import PromptServer

TARGET_KEY = "diffusion_model.txtfusion.projector.weight"
PRESET_FILE = "presets.json"
ROUTE_PATH = "/krea2_projector_delta/presets"


def _preset_path():
    return os.path.join(os.path.dirname(__file__), PRESET_FILE)


def _load_presets_raw():
    path = _preset_path()
    if not os.path.exists(path):
        return {
            "FB2": {
                "values": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.51171875, -0.890625, 0.0, 0.0]
            },
            "FB3": {
                "values": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.51171875, -0.890625, -0.609375, 0.0]
            },
            "FEDOR": {
                "values": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.5116999745368958, -0.8906000256538391, 0.0, 0.0]
            },
            "SKC3VO": {
                "values": [-0.054443359375, -0.1611328125, 0.37109375, 0.50390625, 0.70703125, 0.39453125, 0.3984375, -1.4375, -0.51171875, -0.890625, -0.609375, 0.11279296875]
            }
        }

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _load_presets():
    raw = _load_presets_raw()
    presets = {}
    for name, item in raw.items():
        values = item["values"] if isinstance(item, dict) else item
        if not isinstance(values, list) or len(values) != 12:
            raise ValueError(f"Preset '{name}' must contain exactly 12 values.")
        presets[name] = [float(v) for v in values]
    return presets

@PromptServer.instance.routes.get(ROUTE_PATH)
async def get_krea2_presets(request):
    return web.json_response(_load_presets_raw())

def _parse_custom_values(s):
    if s is None:
        raise ValueError("custom_values is empty.")
    s = str(s).strip()
    if not s:
        raise ValueError("custom_values is empty.")

    try:
        vals = [float(x.strip()) for x in s.replace(";", ",").split(",") if x.strip() != ""]
    except Exception as e:
        raise ValueError("custom_values must be a comma-separated list of numbers.") from e

    if len(vals) != 12:
        raise ValueError("custom_values must contain exactly 12 numbers.")

    return vals


def _make_delta_tensor(values):
    return torch.tensor([values], dtype=torch.float32)


def _format_values(values):
    return ",".join(f"{float(v):.10g}" for v in values)


class Krea2ProjectorDelta:
    @classmethod
    def INPUT_TYPES(cls):
        presets = _load_presets()
        preset_names = list(presets.keys()) if presets else ["FB2"]

        return {
            "required": {
                "model": ("MODEL",),
                "preset": (preset_names, {"default": preset_names[0]}),
                "use_custom": ("BOOLEAN", {"default": False}),
                "custom_values": (
                    "STRING",
                    {
                        "default": "0,0,0,0,0,0,0,0,-0.51171875,-0.890625,0,0",
                        "multiline": False,
                    },
                ),
                "strength": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": -100.0,
                        "max": 100.0,
                        "step": 0.01,
                    },
                ),
            }
        }

    RETURN_TYPES = ("MODEL",)
    RETURN_NAMES = ("model",)
    FUNCTION = "apply"
    CATEGORY = "model_patches/Krea2"
    DESCRIPTION = "Applies a direct (1,12) delta patch to diffusion_model.txtfusion.projector.weight using preset or custom values."

    def _resolve_values(self, preset, use_custom, custom_values):
        if use_custom:
            return _parse_custom_values(custom_values)

        presets = _load_presets()
        if preset not in presets:
            raise ValueError(f"Unknown preset: {preset}")

        return list(presets[preset])

    def apply(self, model, preset, use_custom, custom_values, strength):
        resolved = self._resolve_values(preset, use_custom, custom_values)
        delta = _make_delta_tensor(resolved)

        m = model.clone()
        patch_dict = {TARGET_KEY: (delta,)}
        m.add_patches(patch_dict, strength_patch=float(strength), strength_model=1.0)

        applied_text = _format_values(resolved)

        return {
            "ui": {
                "applied_values": [applied_text]
            },
            "result": (m,)
        }


NODE_CLASS_MAPPINGS = {
    "Krea2 Projector Delta": Krea2ProjectorDelta,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Krea2 Projector Delta": "Krea2 Projector Delta",
}

WEB_DIRECTORY = "./js"