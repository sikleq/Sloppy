// The camera straight down (pitch 90), no terrain following; "topdown_cam" events from the server
// (console "topdown_cam x y distance") move it. Used by scripts/gen/capture_map.py.
(function () {
    function point(x, y, dist) {
        GameUI.SetCameraTerrainAdjustmentEnabled(false);
        GameUI.SetCameraPitchMin(90);
        GameUI.SetCameraPitchMax(90);
        GameUI.SetCameraYaw(0);
        GameUI.SetCameraDistance(dist);
        GameUI.SetCameraLookAtPositionHeightOffset(0);
        GameUI.SetCameraTargetPosition([x, y, 0], 0);
    }
    GameEvents.Subscribe("topdown_cam", function (d) { point(d.x, d.y, d.dist); });
    $.Schedule(1.0, function () { point(0, 0, 6000); });
})();
