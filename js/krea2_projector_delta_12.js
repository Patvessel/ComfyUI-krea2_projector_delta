import { app } from "../../scripts/app.js";

const NODE_NAME = "Krea2 Projector Delta 12";
const PRESET_API = "/krea2_projector_delta/presets";

let presetCache = null;
let presetCachePromise = null;

function getWidget(node, name) {
    return node.widgets?.find((w) => w.name === name);
}

function slotNames() {
    return Array.from({ length: 12 }, (_, i) => `d${i + 1}`);
}

function normalizeValues(values) {
    if (!Array.isArray(values) || values.length !== 12) return null;
    return values.map((v) => Number(v));
}

function setWidgetValue(node, widgetName, value) {
    const widget = getWidget(node, widgetName);
    if (!widget) {
        console.warn(`[${NODE_NAME}] widget not found: ${widgetName}`);
        return;
    }
    widget.value = value;
}

function applyValuesToSlots(node, values) {
    const normalized = normalizeValues(values);
    if (!normalized) {
        console.warn(`[${NODE_NAME}] invalid values for slots`, values);
        return;
    }

    const names = slotNames();
    for (let i = 0; i < names.length; i++) {
        setWidgetValue(node, names[i], normalized[i]);
    }

    node.setDirtyCanvas?.(true, true);
    console.log(`[${NODE_NAME}] applied preset values to slots`, normalized);
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
                const normalized = normalizeValues(values);
                if (normalized) out[name] = normalized;
            }

            console.log(`[${NODE_NAME}] preset map loaded`, out);
            presetCache = out;
            return out;
        })
        .catch((err) => {
            console.error(`[${NODE_NAME}] preset load failed`, err);
            return {};
        })
        .finally(() => {
            presetCachePromise = null;
        });

    return presetCachePromise;
}

async function attachNodeBehavior(node) {
    if (node.comfyClass !== NODE_NAME) return;

    console.log(`[${NODE_NAME}] attachNodeBehavior`, node);

    const presetWidget = getWidget(node, "preset");
    const useCustomWidget = getWidget(node, "use_custom");

    if (!presetWidget || !useCustomWidget) {
        console.warn(`[${NODE_NAME}] preset/use_custom widget missing`, {
            presetWidget,
            useCustomWidget,
            widgets: node.widgets?.map((w) => w.name),
        });
        return;
    }

    const presetMap = await loadPresetMap();

    const originalPresetCallback = presetWidget.callback;
    presetWidget.callback = function (...args) {
        const r = originalPresetCallback?.apply(this, args);

        const presetName = presetWidget.value;
        console.log(`[${NODE_NAME}] preset changed`, presetName, "use_custom=", useCustomWidget.value);

        if (!useCustomWidget.value && presetMap[presetName]) {
            applyValuesToSlots(node, presetMap[presetName]);
        }

        return r;
    };

    const originalUseCustomCallback = useCustomWidget.callback;
    useCustomWidget.callback = function (...args) {
        const r = originalUseCustomCallback?.apply(this, args);

        console.log(`[${NODE_NAME}] use_custom changed`, useCustomWidget.value);

        if (!useCustomWidget.value) {
            const presetName = presetWidget.value;
            if (presetMap[presetName]) {
                applyValuesToSlots(node, presetMap[presetName]);
            }
        }

        return r;
    };

    if (!useCustomWidget.value && presetMap[presetWidget.value]) {
        applyValuesToSlots(node, presetMap[presetWidget.value]);
    }
}

app.registerExtension({
    name: "krea2.projector.delta12.sync",

    async nodeCreated(node) {
        await attachNodeBehavior(node);

        const originalOnExecuted = node.onExecuted;
        node.onExecuted = function (message) {
            originalOnExecuted?.apply(this, arguments);

            const applied = message?.applied_slots?.[0];
            const normalized = normalizeValues(applied);

            console.log(`[${NODE_NAME}] onExecuted message`, message);

            if (normalized) {
                applyValuesToSlots(this, normalized);
            }
        };
    },
});