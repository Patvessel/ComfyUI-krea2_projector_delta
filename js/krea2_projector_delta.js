import { app } from "../../scripts/app.js";

const NODE_NAME = "Krea2 Projector Delta";
const PRESET_API = "/krea2_projector_delta/presets";

let presetCache = null;
let presetCachePromise = null;

function getWidget(node, name) {
    return node.widgets?.find((w) => w.name === name);
}

function setWidgetValue(node, widgetName, value) {
    const widget = getWidget(node, widgetName);
    if (!widget) return;
    widget.value = value;
    widget.callback?.(value);
    node.setDirtyCanvas(true, true);
}

function valuesToString(values) {
    return values.map((v) => Number(v).toString()).join(",");
}

async function loadPresetMap() {
    if (presetCache) return presetCache;
    if (presetCachePromise) return presetCachePromise;

    presetCachePromise = fetch(PRESET_API, { cache: "no-store" })
        .then(async (res) => {
            if (!res.ok) {
                throw new Error(`Failed to load presets: ${res.status}`);
            }
            const data = await res.json();
            const out = {};

            for (const [name, item] of Object.entries(data)) {
                const values = Array.isArray(item) ? item : item.values;
                if (Array.isArray(values) && values.length === 12) {
                    out[name] = valuesToString(values);
                }
            }

            presetCache = out;
            return out;
        })
        .catch((err) => {
            console.error("[Krea2 Projector Delta] preset load failed:", err);
            return {};
        })
        .finally(() => {
            presetCachePromise = null;
        });

    return presetCachePromise;
}

app.registerExtension({
    name: "krea2.projector.delta.sync",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== NODE_NAME) return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

            const presetWidget = getWidget(this, "preset");
            const useCustomWidget = getWidget(this, "use_custom");
            const customWidget = getWidget(this, "custom_values");

            if (!presetWidget || !useCustomWidget || !customWidget) {
                return r;
            }

            loadPresetMap().then((presetMap) => {
                const originalPresetCallback = presetWidget.callback;

                presetWidget.callback = (value, ...args) => {
                    originalPresetCallback?.call(presetWidget, value, ...args);

                    if (!useCustomWidget.value && presetMap[value] !== undefined) {
                        setWidgetValue(this, "custom_values", presetMap[value]);
                    }
                };

                if (!useCustomWidget.value && presetMap[presetWidget.value] !== undefined) {
                    setWidgetValue(this, "custom_values", presetMap[presetWidget.value]);
                }
            });

            return r;
        };

        const onExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            onExecuted?.apply(this, arguments);

            const applied = message?.applied_values?.[0];
            if (applied !== undefined) {
                setWidgetValue(this, "custom_values", applied);
            }
        };
    },
});