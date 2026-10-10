"""sheet.py with the Cirri's live hovering pose added under each frame (CirriModel.setupAnim while hovering, mid
phase), so the frames show what the game draws rather than the bare model. Same arguments as sheet.py; --bare drops
the hovering pose.

    python tools/animations/live_sheet.py cirri --clips happy_loop,greet_air_bow --frames 7 [--view 90]
"""
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheet  # noqa: E402

# radians added to each part's rest rotation: arms drifting out, soft elbows and knees, veils turned out
LIVE = {
    "body": (0.06, 0, 0),
    "neck": (-0.06, 0, 0),
    "right_arm": (-0.25, 0, 0.35), "left_arm": (-0.1, 0, -0.3),
    "right_forearm": (-0.5, 0, 0), "left_forearm": (-0.35, 0, 0),
    "right_leg": (-0.12, 0, 0.04), "left_leg": (-0.05, 0, -0.04),
    "right_shin": (0.3, 0, 0), "left_shin": (0.25, 0, 0),
    "right_veil": (0, 0.45, 0.25), "left_veil": (0, -0.45, -0.25),
}
if "--bare" in sys.argv:
    sys.argv.remove("--bare")
    LIVE = {}

_bare = sheet.posed


def posed(geo, waist, clip, t, mirrored=False):
    g = copy.deepcopy(geo)
    for p in g["parts"]:
        d = LIVE.get(p["name"])
        if d:
            p["rotation"] = [p["rotation"][i] + d[i] for i in range(3)]
    return _bare(g, waist, clip, t, mirrored)


if __name__ == "__main__":
    sheet.posed = posed
    sheet.main()
