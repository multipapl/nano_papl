/* eslint-disable */
// @ts-nocheck
#target photoshop

function main() {
    if (app.documents.length === 0) {
        alert("Error: Please open an image first!");
        return;
    }

    var doc = app.activeDocument;
    var currentRatio = doc.width.as("px") / doc.height.as("px");

    // Presets from your list
    var presets = [
        { name: "P 1:1", w: 1, h: 1 },
        { name: "P 2:3", w: 2, h: 3 },
        { name: "P 3:2", w: 3, h: 2 },
        { name: "P 3:4", w: 3, h: 4 },
        { name: "P 4:3", w: 4, h: 3 },
        { name: "P 4:5", w: 4, h: 5 },
        { name: "P 5:4", w: 5, h: 4 },
        { name: "P 9:16", w: 9, h: 16 },
        { name: "P 16:9", w: 16, h: 9 },
        { name: "P 21:9", w: 21, h: 9 }
    ];

    // Find the best matching preset
    var bestMatch = presets[0];
    var minDiff = Math.abs(currentRatio - (presets[0].w / presets[0].h));

    for (var i = 1; i < presets.length; i++) {
        var diff = Math.abs(currentRatio - (presets[i].w / presets[i].h));
        if (diff < minDiff) {
            minDiff = diff;
            bestMatch = presets[i];
        }
    }

    // UI Window
    var win = new Window("dialog", "AI Crop Assistant");
    win.orientation = "column";
    win.alignChildren = ["fill", "top"];
    win.spacing = 15;
    win.margins = 25;

    var infoGroup = win.add("group");
    infoGroup.orientation = "vertical";
    infoGroup.add("statictext", undefined, "Best matching preset detected:");
    var title = infoGroup.add("statictext", undefined, bestMatch.name);
    title.graphics.font = ScriptUI.newFont("dialog", "BOLD", 24);

    var btnSet = win.add("button", undefined, "PREPARE CROP BOX", { name: "ok" });
    var btnCancel = win.add("button", undefined, "Cancel", { name: "cancel" });

    btnSet.onClick = function () {
        // Step 1: Switch to Crop Tool
        app.currentTool = "cropTool";
        // Step 2: Draw the box with correct ratio (grid-safe dimensions)
        try {
            createCropSelection(bestMatch.w, bestMatch.h);
        } catch (e) { }
        win.close();
    };

    win.center();
    win.show();
}

function createCropSelection(w, h) {
    var doc = app.activeDocument;
    var docW = doc.width.as("px");
    var docH = doc.height.as("px");

    // Calculate initial dimensions based on aspect ratio
    var targetW, targetH;
    if ((docW / docH) > (w / h)) {
        targetH = docH;
        targetW = docH * (w / h);
    } else {
        targetW = docW;
        targetH = docW * (h / w);
    }

    // GRID-SAFE: Round to nearest multiple of 64
    targetW = Math.round(targetW / 64) * 64;
    targetH = Math.round(targetH / 64) * 64;

    // Safety check: ensure dimensions don't exceed canvas bounds
    if (targetW > docW) {
        targetW = Math.floor(docW / 64) * 64;
    }
    if (targetH > docH) {
        targetH = Math.floor(docH / 64) * 64;
    }

    // Calculate centered position with integer coordinates
    var x1 = Math.round((docW - targetW) / 2);
    var y1 = Math.round((docH - targetH) / 2);
    var x2 = x1 + targetW;
    var y2 = y1 + targetH;

    // This creates a selection that Crop Tool will automatically snap to
    doc.selection.select([[x1, y1], [x2, y1], [x2, y2], [x1, y2]]);

    // Trigger the Crop Tool boundary based on selection
    var idsetd = charIDToTypeID("setd");
    var desc = new ActionDescriptor();
    var idnull = charIDToTypeID("null");
    var ref = new ActionReference();
    ref.putClass(charIDToTypeID("Crop"));
    desc.putReference(idnull, ref);
    executeAction(idsetd, desc, DialogModes.NO);

    // Deselect to allow free movement of the crop box
    doc.selection.deselect();
}

function snapTo8(doc) {
    var newW = Math.round(doc.width.as("px") / 8) * 8;
    var newH = Math.round(doc.height.as("px") / 8) * 8;
    doc.resizeImage(UnitValue(newW, "px"), UnitValue(newH, "px"), null, ResampleMethod.BICUBIC);
}

main();