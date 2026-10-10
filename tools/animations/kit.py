"""Authoring kit for the peoples' animation packs (docs/ANIMATIONS.md).

A clip is a list of keyed poses. Angles are degrees ADDED to the live pose (look direction, walk, breathing, the
model's own idle sway), so a pose of zero is "whatever they were already doing". Each channel interpolates only
between its own keys, and every channel starts and ends at rest (zero) unless keyed otherwise, so clips blend in
and out cleanly.

Channels are model part names (see `python tools/animations/compile.py --parts <people>`), plus:

    waist      bends every upper part (the pack's "upper" list) at the hips: bows, leans, slumps
    root       turns the whole body about the feet; root_pos lifts/shifts it (a hop is root_pos=(0, -2, 0))

Short names: ra la (right/left arm), rf lf (forearm), rl ll (leg), rs ls (shin), rft lft (foot),
rla lla (lower arms) and rlf llf (lower forearms), if a model has them.

Conventions, chosen so poses read the same on both sides of the body:

    centre parts (head, body, waist, root, tail, crest, cape, lid, crown, tentacle_N...)   (pitch, yaw, roll)
        pitch + bows / looks down / tips forward; yaw + turns to the person's right; roll + tilts toward their
        left shoulder.
    right_* / left_* parts   (pitch, yaw_out, roll_out)
        pitch - raises the limb forward (-90 points straight ahead, -180 straight up), + swings it back.
        yaw_out + swings a raised arm outward, - across the chest. roll_out + lifts it out to the side.
        Forearms and shins bend at their elbow/knee: a forearm pitch of -60 bends the elbow.
    <part>_pos   model pixels (x, y, z): y - is up, z - is forward; for right_*/left_* parts x + moves it
        away from the body. root_pos moves the whole body.

Once an arm is raised above the shoulder, roll tips it the other way, so a V overhead is easiest as a side
raise: ra=(-10, 0, 160).

    @clip("stretch", "Big stretch", length=3.0, weight=2, require=["adult"])
    def _(c):
        c.key(0.6, ra=(-170, 0, 12), la=(-170, 0, 12), head=(-20, 0, 0), waist=(-8, 0, 0))
        c.hold(0.6, 1.8, ...)        # same pose at both times
        c.key(2.4)                   # every channel used so far back to rest
"""
from __future__ import annotations

import math

TRIGGERS = {"idle", "greet", "farewell", "talk", "listen", "chat_speak", "chat_listen",
            "happy", "thanks", "decline", "pleased", "annoyed", "hurt"}

ALIASES = {"ra": "right_arm", "la": "left_arm", "rf": "right_forearm", "lf": "left_forearm",
           "rl": "right_leg", "ll": "left_leg", "rs": "right_shin", "ls": "left_shin",
           "rft": "right_foot", "lft": "left_foot", "rla": "right_lower_arm", "lla": "left_lower_arm",
           "rlf": "right_lower_forearm", "llf": "left_lower_forearm"}


def part_name(name: str) -> tuple[str, str]:
    """An authoring channel to (part, "rot" | "pos")."""
    kind = "rot"
    if name.endswith("_pos"):
        name, kind = name[:-4], "pos"
    return ALIASES.get(name, name), kind


def _model(part: str, kind: str, value) -> tuple:
    x, y, z = (float(v) for v in value)
    if kind == "rot":
        if part.startswith("left_"):
            return x, -y, -z
        return x, y, z
    if part.startswith("right_"):
        x = -x
    return x, y, z


class Clip:
    def __init__(self, id, name, trigger="idle", length=3.0, weight=1.0, require=(), avoid=(),
                 boost=None, blend=(.25, .35), mirror="hand"):
        if trigger not in TRIGGERS:
            raise ValueError(f"{id}: unknown trigger {trigger}")
        if "," in name:
            raise ValueError(f"{id}: clip names have no commas")
        self.id, self.name, self.trigger, self.length, self.weight = id, name, trigger, float(length), weight
        self.require, self.avoid, self.boost = list(require), list(avoid), dict(boost or {})
        self.blend, self.mirror = tuple(blend), mirror
        self.channels: dict[tuple[str, str], dict[float, tuple]] = {}

    # -- keys -----------------------------------------------------------------------------------------------------
    def key(self, t, **pose):
        """Key every given channel at time t. With no channels, returns every channel used so far to rest."""
        t = round(float(t), 4)
        if t < 0 or t > self.length + 1e-6:
            raise ValueError(f"{self.id}: key {t} outside 0..{self.length}")
        if not pose:
            for keys in self.channels.values():
                keys[t] = (0.0, 0.0, 0.0)
            return self
        for name, value in pose.items():
            part, kind = part_name(name)
            if kind == "pos" and part == "waist":
                raise ValueError(f"{self.id}: the waist only rotates")
            self.channels.setdefault((part, kind), {})[t] = _model(part, kind, value)
        return self

    def hold(self, start, end, **pose):
        return self.key(start, **pose).key(end, **pose)

    def rest(self, t, *names):
        """Return just these channels to rest at t."""
        t = round(float(t), 4)
        for name in names:
            part, kind = part_name(name)
            self.channels.setdefault((part, kind), {})[t] = (0.0, 0.0, 0.0)
        return self

    def cycle(self, start, end, period, a, b, end_on="a"):
        """Alternate between pose dicts a and b every half period from start to end."""
        t, flip = start, False
        while t < end - 1e-6:
            self.key(t, **(b if flip else a))
            t += period / 2
            flip = not flip
        self.key(end, **(a if end_on == "a" else b))
        return self

    def wobble(self, start, end, rate, channel, amplitude, base=(0, 0, 0), axis=0, decay=0.0):
        """A small oscillation on one component (shivers, giggles, scratching, a tail flick)."""
        steps = max(2, int((end - start) * rate * 2))
        for i in range(steps + 1):
            t = start + (end - start) * i / steps
            sign = 0 if i in (0, steps) else (1 if i % 2 else -1)
            v = list(base)
            v[axis] += sign * amplitude * (1 - decay * i / steps)
            self.key(t, **{channel: tuple(v)})
        return self

    def wave(self, start, end, period, channel, amplitude, base=(0, 0, 0), axis=0, phase=0.0, steps_per_period=8):
        """A smooth sine on one component (swaying, bobbing, tentacles rippling)."""
        n = max(2, int((end - start) / period * steps_per_period))
        for i in range(n + 1):
            t = start + (end - start) * i / n
            v = list(base)
            fade = min(1.0, (t - start) / (period / 2), (end - t) / (period / 2))
            v[axis] += amplitude * math.sin(((t - start) / period + phase) * math.tau) * max(0.0, fade)
            self.key(t, **{channel: tuple(v)})
        return self

    # -- output ---------------------------------------------------------------------------------------------------
    def parts(self):
        return {part for part, _ in self.channels}

    def compile(self):
        tracks = {}
        for (part, kind), keys in sorted(self.channels.items()):
            keys = dict(keys)
            if min(keys) > 0:
                keys[0.0] = (0.0, 0.0, 0.0)
            if max(keys) < self.length - 1e-6:
                keys[round(self.length, 4)] = (0.0, 0.0, 0.0)
            tracks[f"{part}.{kind}"] = [[t, *[round(v, 3) for v in keys[t]]] for t in sorted(keys)]
        out = {"id": self.id, "name": self.name, "trigger": self.trigger, "length": round(self.length, 3),
               "weight": self.weight}
        if self.require:
            out["require"] = self.require
        if self.avoid:
            out["avoid"] = self.avoid
        if self.boost:
            out["boost"] = self.boost
        if self.blend != (.25, .35):
            out["blend"] = list(self.blend)
        if self.mirror != "hand":
            out["mirror"] = self.mirror
        out["tracks"] = tracks
        return out


CLIPS: list[Clip] = []


def clip(id, name, also=None, **options):
    """Decorator: the function receives a fresh Clip to key, and the clip joins the pack.

    ``also`` maps extra clip ids to other triggers (``also={"nod_listen": "chat_listen"}``), so one motion can
    serve several moments without copying its keys. Each counts as a clip of its own.
    """
    def register(fn):
        c = Clip(id, name, **options)
        fn(c)
        CLIPS.append(c)
        for other_id, trigger in (also or {}).items():
            twin = Clip(other_id, name, **{**options, "trigger": trigger})
            twin.channels = c.channels
            CLIPS.append(twin)
        return c
    return register


def sine(t, period, phase=0.0):
    return math.sin((t / period + phase) * math.tau)
