# Krea2 Projector Delta

A lightweight ComfyUI custom node that applies a direct (1,12) delta patch to diffusion_model.txtfusion.projector.weight, with editable presets, custom value input, and a LoRA-style strength control.
Features

Preset-based control for known (1,12) projector deltas such as FB2, FB3, FEDOR, and SKC3VO-style values.

Custom mode for manually entering 12 comma-separated values ​​when a preset is not enough.

Strength control that scales the selected delta before patching the model, similar to how LoRA patch strength is applied in ComfyUI.

Editable external preset storage via presets.json, so presets can be added or modified without changing Python code.

Optional JavaScript UI sync so the custom value field can reflect the preset or last applied values ​​after execution.

# What it does

This node is designed for cases where the effective modification can be expressed as a very small direct delta rather than a large adapter file. It patches a single target weight, diffusion_model.txtfusion.projector.weight, using a 12-value vector shaped as (1,12), then applies the patch through ComfyUI's model patching flow.

In practice, that makes it useful when several tiny preset files are really just different parameterizations of the same small control space. Instead of swapping multiple tiny files, the node exposes that control directly in the graph.

# Installation

Clone or copy this repository into your ComfyUI/custom_nodes/ directory.

Ensure the folder contains the Python node file, presets.json, and the js/ directory if UI sync is enabled.

Restart ComfyUI so the backend node and frontend JavaScript extension are loaded.

Example:

bash
git clone https://github.com/yourname/krea2-projector-delta.git ComfyUI/custom_nodes/krea2-projector-delta

# Files

text
krea2-projector-delta/
├─ __init__.py
├─ krea2_projector_delta.py
├─ presets.json
└─js/
└─ krea2_projector_delta.js

# Usage

Load a compatible Krea 2 model in ComfyUI.

Insert Krea2 Projector Delta between the model loader and the sampler.

Choose a preset, or enable use_custom and enter 12 comma-separated values.

Adjust strength to scale the effect up or down.

Run the workflow and compare outputs using the same seed when testing different settings.

# Presets

Presets are loaded from presets.json so they can be edited without touching the node code. Each preset should provide exactly 12 numeric values, either as a simple array or as an object with a values field.

Simple format:

json
{
"FB2": [0, 0, 0, 0, 0, 0, 0, 0, -0.51171875, -0.890625, 0, 0]
}

Extended format:

json
{
"FB2": {
"values": [0, 0, 0, 0, 0, 0, 0, 0, -0.51171875, -0.890625, 0, 0],
"comment": "raw diff; cols 9 and 10 only"
}
}

After changing preset names, refresh or restart ComfyUI so the dropdown is rebuilt from the updated data.

# UI behavior

If the JavaScript extension is enabled, preset selection can populate the custom values ​​field automatically, and node execution can write the last applied values ​​back into that field. This helps keep the visible text box aligned with the preset or custom values ​​actually used during the previous run.

# Notes
This project assumes the target model exposes diffusion_model.txtfusion.projector.weight and that the intended patch is a direct (1,12) delta. 

Because ComfyUI's frontend and backend are loaded separately, changes to node inputs, preset lists, or frontend extension behavior may require a restart or full browser refresh before they appear correctly.

# Credits
This node design is based on community analysis comparing tiny Krea 2 projector delta files and equivalent LoRA-style encoding.

# See the link for reference
https://www.reddit.com/r/StableDiffusion/comments/1ul38ei/made_yet_another_bypass_filter_for_krea_2_this/
https://www.reddit.com/r/StableDiffusion/comments/1ukh334/i_extracted_the_values_of_krea_2_safery_filters/
https://www.reddit.com/r/StableDiffusion/comments/1ueacq2/comment/otix1aa/
https://civitai.red/models/2728234/krea2filterbypass?modelVersionId=3067151
