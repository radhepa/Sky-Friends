from kit import clip
import math

# Everyday moments of the Cirri, grown-ups: things done in the air by a light, musical, curious people who never
# land. Under every clip is the live hovering pose (CirriModel): arms afloat about 20 degrees out with soft elbows,
# legs hanging with soft knees, veils waving behind; the poses below allow for it (an arm "hanging straight" is
# ra=(14, 0, -16), rf=(25, 0, 0)). A Cirri's legs and veils hang from its body, so the root (which turns about the
# hips) tips the whole figure; veils and hair are counter-turned to keep hanging, and the big turns go about the
# body's middle (turn_pose). Waist bends are not used: the root says the same thing here.

HIP = 13.0   # the pack's hip height: the root turns about it
MID = 7.0    # a grown-up's middle (between bun and toes): somersaults and rolls turn about it


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def env(t, t0, t1, fade):
    """0 -> 1 -> 0: eases in from t0 over `fade` seconds and out again to t1."""
    if t <= t0 or t >= t1:
        return 0.0
    return min(smooth((t - t0) / fade), smooth((t1 - t) / fade))


def sn(t, period, phase=0.0):
    return math.sin((t / period + phase) * math.tau)


def sampled(c, t0, t1, fn, step=0.1):
    """Key every channel fn(t) returns, every `step` seconds from t0 to t1."""
    n = max(1, round((t1 - t0) / step))
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        pose = fn(t)
        if pose:
            c.key(t, **{k: tuple(v) for k, v in pose.items()})
    return c


def turn_pose(angle, axis, mid=MID):
    """The root rotation and root_pos for a turn of `angle` degrees (axis 0 pitch, 1 yaw, 2 roll) about the body's
    middle instead of the hips."""
    a = math.radians(angle)
    d = mid - HIP
    rot = [0.0, 0.0, 0.0]
    rot[axis] = angle
    if axis == 0:
        pos = (0.0, d - d * math.cos(a), -d * math.sin(a))
    elif axis == 2:
        pos = (d * math.sin(a), d - d * math.cos(a), 0.0)
    else:
        pos = (0.0, 0.0, 0.0)
    return tuple(rot), pos


def full_turn(c, t0, t1, axis, sign=1, mid=MID, step=0.1, ease=smooth, extra=None):
    """One whole turn of the body between t0 and t1 (eased in and out). Euler angles can't come back round to zero
    by a smooth path, so the angle runs on to 360 and steps back to 0 a ten-thousandth of a second later, when the
    body is upright again in the very same orientation (and at rest, so nothing shows). `extra(t, angle)` may add
    to the root's other axes during the turn."""
    def pose(t):
        angle = sign * 360 * ease((t - t0) / (t1 - t0))
        rot, pos = turn_pose(angle, axis, mid)
        if extra:
            rot = tuple(r + e for r, e in zip(rot, extra(t, angle)))
        return dict(root=rot, root_pos=pos)
    sampled(c, t0, t1, pose, step)
    c.key(t1 + 0.0001, root=(0, 0, 0), root_pos=(0, 0, 0))


def lean(c, t, angle, **pose):
    """Tip the whole body forward (+) or back (-) about its middle, with the veils and hair counter-turned."""
    rot, pos = turn_pose(angle, 0)
    c.key(t, root=rot, root_pos=pos, **pose)


ADULT = ["adult"]
FLIGHTY = {"manner:flighty": 3}
SHY = {"manner:shy": 3}
RESTLESS = {"manner:restless": 2}

# poses worked out on the live model (right side; mirror by swapping r/l)
CHEST_R = dict(ra=(-25, -45, -20), rf=(-80, 0, 0))                     # right hand flat on the chest
CHEST_L = dict(la=(-30, -45, -17), lf=(-88, 0, 0))
SHADE_R = dict(ra=(-76, -30, -20), rf=(-61, 0, 0))                     # hand at the brow
CROSSED = dict(ra=(-30, -50, -20), rf=(-70, 0, 0), la=(-30, -50, -17), lf=(-80, 0, 0))
CUPPED = dict(ra=(-40, -35, -20), rf=(-50, 0, 0), la=(-40, -35, -17), lf=(-55, 0, 0))
BEHIND_HEAD = dict(ra=(-160, 40, 0), rf=(-120, 0, 0), la=(-160, 40, 0), lf=(-120, 0, 0))
TUCK = dict(rl=(-80, 0, 0), ll=(-80, 0, 0), rs=(100, 0, 0), ls=(100, 0, 0))
HUG_SHINS = dict(ra=(-45, -25, -20), la=(-45, -25, -17), rf=(-50, 0, 0), lf=(-50, 0, 0))
STRAIGHT_LEGS = dict(rl=(10, 0, -2), ll=(4, 0, 2), rs=(-17, 0, 0), ls=(-14, 0, 0))
# with a hand raised overhead the wrist ribbons would stand up stiff: let them flop back down
DROOP_R = dict(right_ribbon=(120, 0, 0), right_ribbon2=(30, 0, 0))
DROOP_L = dict(left_ribbon=(120, 0, 0), left_ribbon2=(30, 0, 0))
RIBBONS_REST = dict(right_ribbon=(0, 0, 0), right_ribbon2=(0, 0, 0), left_ribbon=(0, 0, 0), left_ribbon2=(0, 0, 0))


# -- big, showy, airborne ------------------------------------------------------------------------------------------

@clip("veil_stretch", "Long stretch with the veils", length=4.2, weight=3, require=ADULT, mirror="free")
def _(c):
    # arms float up into a long V, the back arches, the toes point and the veils lift out like wings
    up = dict(ra=(-10, 0, 150), la=(-10, 0, 150), rf=(29, 0, 0), lf=(20, 0, 0))
    c.key(0.9, **DROOP_R, **DROOP_L)
    c.key(2.2, **DROOP_R, **DROOP_L)
    c.key(2.9, **RIBBONS_REST)
    c.key(0.9, root=(-10, 0, 0), head=(-18, 0, 0), hair=(26, 0, 0), rl=(10, 0, 0), ll=(10, 0, 0),
          rs=(-17, 0, 0), ls=(-14, 0, 0), right_veil=(8, 0, 30), left_veil=(8, 0, 30), root_pos=(0, -1.5, 0), **up)
    c.wobble(0.9, 2.2, 5, "ra", 3, base=up["ra"], axis=2)
    c.key(2.2, root=(-12, 0, 0), head=(-22, 0, 0), hair=(30, 0, 0), right_veil=(10, 0, 40), left_veil=(10, 0, 40),
          la=(-10, 0, 154), root_pos=(0, -2, 0))
    # and let go: arms float down wide, a little sink, the veils settle last
    c.key(3.0, ra=(-6, 0, 50), la=(-6, 0, 50), rf=(0, 0, 0), lf=(0, 0, 0), root=(2, 0, 0), head=(4, 0, 0),
          hair=(-4, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0), root_pos=(0, 0.6, 0),
          right_veil=(0, 0, 20), left_veil=(0, 0, 20))
    c.key(3.6, ra=(0, 0, 0), la=(0, 0, 0), root=(0, 0, 0), head=(0, 0, 0), hair=(0, 0, 0), root_pos=(0, 0, 0))
    c.key(4.2)


@clip("slow_somersault", "Slow somersault", length=4.0, weight=2, require=ADULT, avoid=["manner:shy"],
      boost=FLIGHTY, mirror="never")
def _(c):
    # knees up and hugged, head tucked, and over they go, slowly, about their middle; then unfurl
    tuck = dict(head=(25, 0, 0), **TUCK, **HUG_SHINS)
    c.key(0.5, rl=(-20, 0, 0), ll=(-20, 0, 0), ra=(-30, 0, 20), la=(-30, 0, 20), head=(10, 0, 0))
    c.key(1.0, **tuck)
    c.key(2.6, **tuck)
    full_turn(c, 0.6, 3.1, 0)
    # the veils and hair stream out behind the turn and catch up after it
    c.key(1.6, right_veil=(40, 0, 20), left_veil=(40, 0, 20), hair=(40, 0, 0))
    c.key(2.4, right_veil=(30, 0, 25), left_veil=(30, 0, 25), hair=(30, 0, 0))
    c.key(3.3, rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0), ra=(-10, 0, 40), la=(-10, 0, 40),
          rf=(0, 0, 0), lf=(0, 0, 0), head=(-6, 0, 0), right_veil=(-15, 0, 10), left_veil=(-15, 0, 10),
          hair=(-10, 0, 0))
    c.key(4.0)


@clip("barrel_roll", "Lazy barrel roll", length=3.8, weight=2, require=ADULT, avoid=["manner:shy"], boost=FLIGHTY,
      mirror="free")
def _(c):
    # arms spread like a gliding bird, legs long and together, one lazy roll over to the side
    spread = dict(ra=(0, 0, 60), la=(0, 0, 63), rf=(25, 0, 0), lf=(18, 0, 0), right_veil=(10, 0, 35),
                  left_veil=(10, 0, 35), **STRAIGHT_LEGS)
    c.key(0.5, head=(0, 0, 8), **spread)
    c.key(1.6, head=(0, 0, 14))
    c.key(2.8, head=(0, 0, 6), **spread)
    full_turn(c, 0.45, 3.05, 2)
    c.key(3.3, ra=(0, 0, 12), la=(0, 0, 12), rf=(0, 0, 0), lf=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0),
          ls=(0, 0, 0), head=(0, 0, -4), right_veil=(0, 0, -10), left_veil=(0, 0, 18))
    c.key(3.8)


@clip("arms_out_spin", "Spins with arms out", length=3.6, weight=2, require=ADULT, avoid=["manner:shy"],
      boost=FLIGHTY, mirror="free")
def _(c):
    # a whole turn on the spot with arms wide and head back; the veils fly out all round
    wide = dict(ra=(-8, 0, 66), la=(-6, 0, 70), rf=(25, 0, 0), lf=(18, 0, 0), head=(-14, 0, 0), hair=(20, 0, 0),
                right_veil=(25, 0, 45), left_veil=(25, 0, 45), rl=(6, 0, -2), ll=(6, 0, 2), rs=(-10, 0, 0),
                ls=(-8, 0, 0))
    c.key(0.45, **wide)
    c.key(2.7, **wide)
    full_turn(c, 0.35, 3.0, 1, extra=lambda t, a: (0, 0, 6 * math.sin(math.radians(a / 2))))
    c.key(3.15, ra=(0, 0, 20), la=(0, 0, 20), rf=(0, 0, 0), lf=(0, 0, 0), head=(4, 0, 4), hair=(-6, 0, 0),
          right_veil=(-10, 0, 15), left_veil=(-10, 0, 15), rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0),
          ls=(0, 0, 0))
    c.key(3.6)


@clip("float_on_back", "Floats on the back", length=6.0, weight=2, require=ADULT, mirror="free")
def _(c):
    # lies back on the air, hands behind the head, one knee up, bobbing like a leaf on a pond
    def pose(t):
        e = env(t, 0, 6.0, 1.2)
        rot, pos = turn_pose(-72 * e, 0)
        bob = 0.5 * sn(t, 2.4) * e
        return dict(root=(rot[0], 0, 3 * sn(t, 4.8) * e), root_pos=(pos[0], pos[1] + bob, pos[2]),
                    right_veil=(70 * e, 0, 10 * e), left_veil=(70 * e, 0, 10 * e),
                    hair=(60 * e, 0, 0), head=(8 * e, 0, 0),
                    rl=(-45 * e, 0, 0), rs=(70 * e, 0, 0), ll=(4 * e, 0, 0), ls=(-14 * e, 0, 0))
    sampled(c, 0, 6.0, pose, step=0.2)
    c.key(1.0, **BEHIND_HEAD)
    c.key(4.9, **BEHIND_HEAD)
    c.key(5.6, ra=(0, 0, 0), la=(0, 0, 0), rf=(0, 0, 0), lf=(0, 0, 0))


@clip("knees_up_float", "Tucks the knees up and floats", length=5.6, weight=2, require=ADULT, mirror="free")
def _(c):
    # curled round the knees like a seed on the wind, rocking slowly, cheek on the knees
    c.key(0.9, head=(22, 0, 8), **TUCK, **HUG_SHINS)

    def rock(t):
        e = env(t, 0.9, 4.6, 0.8)
        return dict(root=(5 * sn(t - 0.9, 2.6) * e, 0, 3 * sn(t - 0.9, 5.2) * e),
                    root_pos=(0, 0.6 * sn(t - 0.9, 2.6, 0.25) * e, 0),
                    right_veil=(-5 * sn(t - 0.9, 2.6) * e, 0, 0), left_veil=(-5 * sn(t - 0.9, 2.6) * e, 0, 0))
    sampled(c, 0.9, 4.6, rock, step=0.15)
    c.key(4.6, head=(18, 0, 10), **TUCK, **HUG_SHINS)
    c.key(5.2, rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0), ra=(0, 0, 0), la=(0, 0, 0), rf=(0, 0, 0),
          lf=(0, 0, 0), head=(0, 0, 0))
    c.key(5.6)


@clip("swim_kick", "Swims on the air", length=4.6, weight=2, require=ADULT, boost=RESTLESS, mirror="free")
def _(c):
    # tips forward and swims two lazy breaststrokes, the legs fluttering behind
    reach = dict(ra=(-150, -6, -20), la=(-150, -6, -17), rf=(29, 0, 0), lf=(20, 0, 0))
    sweep = dict(ra=(-95, 55, 10), la=(-95, 55, 10), rf=(10, 0, 0), lf=(5, 0, 0))
    pull = dict(ra=(-40, -30, -20), la=(-40, -30, -17), rf=(-80, 0, 0), lf=(-85, 0, 0))
    lean(c, 0.6, 30, head=(-28, 0, 0), hair=(-10, 0, 0), **pull)
    for t0 in (0.9, 2.2):
        c.key(t0 + 0.3, **reach)
        c.key(t0 + 0.75, **sweep)
        c.key(t0 + 1.2, **pull)
    lean(c, 3.5, 30, head=(-28, 0, 0), hair=(-10, 0, 0))
    c.wave(0.6, 3.6, 0.55, "rl", 22, axis=0)
    c.wave(0.6, 3.6, 0.55, "ll", 22, axis=0, phase=0.5)
    c.wave(0.6, 3.6, 0.55, "rs", 12, base=(-10, 0, 0), axis=0, phase=0.15)
    c.wave(0.6, 3.6, 0.55, "ls", 12, base=(-10, 0, 0), axis=0, phase=0.65)
    lean(c, 4.1, 0, head=(0, 0, 0), hair=(0, 0, 0), ra=(0, 0, 0), la=(0, 0, 0), rf=(0, 0, 0), lf=(0, 0, 0))
    c.key(4.6)


@clip("look_down_below", "Peers down at the ground far below", length=5.2, weight=2, require=ADULT)
def _(c):
    # tips over to look past the toes at the land far below: fields, a river, walkers' roofs. So small!
    lean(c, 1.0, 28, head=(34, -6, 0), hair=(-40, 0, 0), right_veil=(-25, 0, 0), left_veil=(-25, 0, 0),
         rl=(-20, 0, 0), ll=(-14, 0, 0), ra=(0, 0, 18), la=(0, 0, 18))
    c.key(2.2, head=(36, 14, 4))
    c.key(3.2, head=(34, -16, -4))
    # a slow, wondering shake of the head
    c.key(3.6, head=(30, 6, 0))
    c.key(3.9, head=(30, -6, 0))
    lean(c, 4.2, 22, head=(26, 0, 0))
    lean(c, 4.7, 0, head=(0, 0, 0), hair=(0, 0, 0), right_veil=(0, 0, 0), left_veil=(0, 0, 0), rl=(0, 0, 0),
         ll=(0, 0, 0), ra=(0, 0, 0), la=(0, 0, 0))
    c.key(5.2)


@clip("whale_watch", "Shades the eyes to watch for whales", length=5.6, weight=2, require=ADULT)
def _(c):
    # a hand to the brow, rising a little to see further, a slow sweep along the horizon... was that a whale?
    c.key(0.7, head=(-8, -24, 0), root_pos=(0, -1, 0), **SHADE_R)
    c.key(2.0, head=(-10, 6, 0), root=(0, 8, 0), root_pos=(0, -2, 0), hair=(10, 0, 0))
    c.key(3.0, head=(-12, 26, 3), root=(0, 14, 0), root_pos=(0, -2.5, 0), ra=(-80, -26, -20))
    c.key(3.6, head=(-14, 30, 3), root=(0, 15, 0), root_pos=(0, -3, 0), hair=(12, 0, 0))
    # not a whale: just a cloud. The hand comes down and they settle
    c.key(4.3, head=(2, 10, 0), root=(0, 5, 0), root_pos=(0, -0.5, 0), ra=(-20, -10, -6), rf=(-15, 0, 0),
          hair=(0, 0, 0))
    c.key(4.9, head=(0, 0, 0), root=(0, 0, 0), root_pos=(0, 0, 0), ra=(0, 0, 0), rf=(0, 0, 0))
    c.key(5.6)


@clip("catch_breeze", "Catches a breeze in an open palm", length=4.8, weight=2, require=ADULT, mirror="hand")
def _(c):
    # the left hand opens out to the side, palm up; the wrist ribbon lifts in the breeze; the fingers close
    # round it and bring it in to the heart
    c.key(0.8, la=(-55, 45, 20), lf=(15, 0, 0), head=(6, -30, -6))
    c.wobble(0.8, 2.2, 4, "left_ribbon", 18, base=(-40, 0, 0), axis=0)
    c.wobble(0.8, 2.2, 4, "left_ribbon2", 22, base=(-20, 0, 0), axis=0)
    c.key(1.6, la=(-58, 48, 22), head=(4, -34, -8))
    c.key(2.2, la=(-55, 45, 20), lf=(-40, 0, 0), head=(8, -30, -4), root_pos=(0, -0.5, 0))
    c.key(3.0, head=(10, -6, 4), root_pos=(0, 0, 0), **CHEST_L)
    c.key(3.5, head=(6, 0, 6), root=(0, 0, 2))
    c.key(4.2, la=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0), root=(0, 0, 0))
    c.key(4.8)


@clip("hum_hand_on_chest", "Hums with a hand on the chest", length=5.6, weight=3, require=ADULT)
def _(c):
    # eyes closed (the head tipped back), a hand on the heart, swaying to a tune only they can hear
    c.key(0.7, la=(0, 0, 8), **CHEST_R)

    def hum(t):
        e = env(t, 0.3, 5.1, 0.9)
        return dict(head=(-18 * e, 4 * sn(t, 3.6) * e, 7 * sn(t, 1.8) * e),
                    hair=(18 * e, 0, -5 * sn(t, 1.8) * e),
                    root=(0, 0, 3 * sn(t, 1.8, -0.1) * e),
                    root_pos=(0, 0.4 * sn(t, 0.9) * e, 0))
    sampled(c, 0.3, 5.1, hum, step=0.15)
    c.key(4.6, la=(0, 0, 8), **CHEST_R)
    c.key(5.1, ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0))
    c.key(5.6)


@clip("count_clouds", "Counts clouds", length=5.2, weight=2, require=ADULT)
def _(c):
    # a finger up at the clouds: one, two, three, four... and a pleased little nod
    c.key(0.7, ra=(-128, -20, -20), rf=(29, 0, 0), head=(-26, -14, 0), hair=(20, 0, 0), **DROOP_R)
    c.key(3.6, **DROOP_R)
    c.key(4.1, right_ribbon=(0, 0, 0), right_ribbon2=(0, 0, 0))
    for i, yaw in enumerate((-20, -4, 12, 28)):
        t = 0.8 + i * 0.8
        c.key(t, ra=(-128, yaw, -20), head=(-26, yaw * 0.7, 0))
        c.key(t + 0.2, ra=(-120, yaw, -20), head=(-23, yaw * 0.7, 0))
        c.key(t + 0.4, ra=(-128, yaw + 4, -20), head=(-26, yaw * 0.7 + 2, 0))
    c.key(4.0, ra=(-30, 0, -6), rf=(-10, 0, 0), head=(4, 6, 0), hair=(0, 0, 0))
    c.key(4.3, head=(-4, 4, 0))
    c.key(4.6, ra=(0, 0, 0), rf=(0, 0, 0), head=(0, 0, 0))
    c.key(5.2)


@clip("yawn_stretch", "Yawns and stretches", length=4.6, weight=2, require=ADULT)
def _(c):
    # a hand to the mouth, a big yawn with the head back, then both arms out wide and a shake to wake up
    c.key(0.6, ra=(-60, -45, -20), rf=(-95, 0, 0), head=(-6, 0, 0))
    c.key(1.4, ra=(-62, -45, -20), rf=(-98, 0, 0), head=(-26, 0, -6), hair=(24, 0, 0), root=(-4, 0, 0),
          root_pos=(0, -0.6, 0))
    c.key(2.1, ra=(10, 10, 55), rf=(25, 0, 0), la=(10, 10, 58), lf=(18, 0, 0), head=(-12, 0, 0), hair=(10, 0, 0),
          root=(-8, 0, 0), rs=(-17, 0, 0), ls=(-14, 0, 0), rl=(10, 0, 0), ll=(10, 0, 0))
    c.key(2.7, ra=(14, 12, 60), la=(14, 12, 62), root=(-9, 0, 0))
    c.wobble(2.8, 3.5, 7, "root", 2.5, axis=2, decay=0.6)
    c.key(3.5, ra=(0, 0, 10), rf=(0, 0, 0), la=(0, 0, 10), lf=(0, 0, 0), head=(4, 0, 0), hair=(0, 0, 0),
          rs=(0, 0, 0), ls=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0), root_pos=(0, 0, 0))
    c.key(4.0, ra=(0, 0, 0), la=(0, 0, 0), head=(0, 0, 0))
    c.key(4.6)


@clip("braid_hair", "Braids the hair tail", length=5.4, weight=2, require=ADULT, boost=RESTLESS, mirror="free")
def _(c):
    # hands behind the head working a plait, head bowed to let them reach; then a toss to settle it
    work = dict(ra=(-150, 40, -45), rf=(-115, 0, 0), la=(-150, 40, -42), lf=(-115, 0, 0))
    c.key(0.8, head=(14, 8, 0), hair=(-10, 0, 0), **work)
    for i in range(6):
        t = 1.0 + i * 0.45
        s = 1 if i % 2 else -1
        c.key(t, ra=(-150 + 6 * s, 40, -45), la=(-150 - 6 * s, 40, -42), hair2=(0, 0, 6 * s), hair=(-10, 0, 2 * s))
    c.key(3.8, head=(10, 4, 0), hair=(-8, 0, 0), hair2=(0, 0, 0), **work)
    # the toss: hands drop away and the head flicks back, the tail swings
    c.key(4.2, ra=(0, 0, 20), rf=(0, 0, 0), la=(0, 0, 20), lf=(0, 0, 0), head=(-10, -10, 4), hair=(26, 0, 0))
    c.key(4.6, head=(2, 0, 0), hair=(-12, 0, 0), hair2=(10, 0, 0))
    c.key(5.0, ra=(0, 0, 0), la=(0, 0, 0), head=(0, 0, 0), hair=(4, 0, 0), hair2=(-4, 0, 0))
    c.key(5.4)


# a veil laid forward over the shoulder to hang down the front (root segment over the shoulder, the rest hanging)
DRAPE_R = dict(right_veil=(-110, -26, -4), right_veil2=(93, 0, 0), right_veil3=(-7, 0, 0), right_veil4=(-7, 0, 0))
DRAPE_L = dict(left_veil=(-110, -26, -4), left_veil2=(93, 0, 0), left_veil3=(-7, 0, 0), left_veil4=(-7, 0, 0))
VEILS_REST = dict(right_veil=(0, 0, 0), right_veil2=(0, 0, 0), right_veil3=(0, 0, 0), right_veil4=(0, 0, 0),
                  left_veil=(0, 0, 0), left_veil2=(0, 0, 0), left_veil3=(0, 0, 0), left_veil4=(0, 0, 0))


@clip("smooth_veil", "Smooths a veil", length=5.2, weight=2, require=ADULT)
def _(c):
    # the right veil is laid forward over the shoulder and both hands smooth it down the front, twice
    high = dict(ra=(-55, -10, -20), rf=(-75, 0, 0), la=(-60, -58, -17), lf=(-70, 0, 0))
    low = dict(ra=(-22, -12, -20), rf=(-35, 0, 0), la=(-32, -50, -17), lf=(-35, 0, 0))
    c.key(0.5, ra=(-120, -20, -10), rf=(-60, 0, 0), head=(6, 24, 0))
    c.key(0.9, head=(20, 22, 0), **DRAPE_R, **high)
    for t in (1.0, 2.4):
        c.key(t, head=(18, 22, 0), **high)
        c.key(t + 1.0, head=(28, 20, 0), **low)
    c.key(3.8, head=(16, 20, 0), **DRAPE_R, **high)
    # and flicked back over the shoulder to float free
    c.key(4.2, ra=(-130, -10, -10), rf=(-40, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), right_veil=(-40, 0, 20),
          right_veil2=(20, 0, 0), right_veil3=(0, 0, 0), right_veil4=(0, 0, 0), head=(0, 10, 0))
    c.key(4.7, ra=(0, 0, 0), rf=(0, 0, 0), right_veil=(8, 0, 4), right_veil2=(-6, 0, 0), head=(0, 0, 0))
    c.key(5.2)


@clip("gather_veils", "Gathers the veils against a breeze", length=4.8, weight=2, require=ADULT)
def _(c):
    # a chilly gust from Borre: both veils drawn forward round the shoulders like a shawl, a hunch, a shiver,
    # then they float free again
    shawl = dict(**DRAPE_R, **DRAPE_L, **CROSSED)
    c.key(0.4, ra=(-100, -20, -10), rf=(-60, 0, 0), la=(-100, -20, -10), lf=(-60, 0, 0), head=(6, 0, 0))
    c.key(0.8, head=(14, -18, 0), root=(6, 0, 0), **shawl)
    c.wobble(0.9, 2.4, 9, "root", 1.6, base=(6, 0, 0), axis=2)
    c.key(2.4, head=(16, -22, -4), root=(6, 0, 0), root_pos=(0, 0.4, 0), **shawl)
    c.key(3.0, head=(4, 0, 0), **shawl)
    c.key(3.6, ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0), root=(0, 0, 0),
          root_pos=(0, 0, 0), **VEILS_REST)
    c.key(4.8)


@clip("peek_peach", "Peeks at a peach", length=5.0, weight=2, require=ADULT)
def _(c):
    # a sky peach kept in the sash: out it comes in cupped hands, a sniff, a happy wiggle, and back it goes
    c.key(0.6, ra=(-15, -40, -20), rf=(-60, 0, 0), head=(24, 0, 0), sash=(-14, 0, 0))
    c.key(1.2, head=(18, 0, 0), sash=(0, 0, 0), **CUPPED)
    c.key(1.8, head=(6, 0, 0), ra=(-62, -35, -20), rf=(-70, 0, 0), la=(-62, -35, -17), lf=(-75, 0, 0))
    c.key(2.05, head=(10, 0, 0))
    c.key(2.3, head=(5, 0, 0))
    c.key(2.55, head=(10, 0, 0))
    c.wobble(2.6, 3.4, 6, "root", 3, axis=2, decay=0.3)
    c.key(3.4, head=(-6, 0, 5), root_pos=(0, -0.6, 0))
    c.key(3.9, ra=(-15, -40, -20), rf=(-60, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), head=(20, 0, 0), sash=(-12, 0, 0),
          root_pos=(0, 0, 0))
    c.key(4.2, ra=(-12, -38, -20), sash=(0, 0, 0))
    c.key(4.6, ra=(0, 0, 0), rf=(0, 0, 0), head=(0, 0, 0))
    c.key(5.0)


# -- small and self-conscious ----------------------------------------------------------------------------------------

@clip("adjust_ribbon", "Adjusts a wrist ribbon", length=3.8, weight=1, require=ADULT,
      boost={"manner:shy": 3, "manner:restless": 2})
def _(c):
    # the left wrist comes up in front; the right hand tugs the ribbon straight, once, twice; a glance to check
    c.key(0.6, la=(-45, -30, -17), lf=(-60, 0, 0), ra=(-40, -42, -20), rf=(-55, 0, 0), head=(24, -10, 0))
    for t in (0.9, 1.4, 1.9):
        c.key(t, rf=(-65, 0, 0), left_ribbon=(-30, 0, 0))
        c.key(t + 0.2, rf=(-50, 0, 0), left_ribbon=(10, 0, 0), left_ribbon2=(-20, 0, 0))
    c.key(2.4, ra=(-10, 0, 0), rf=(-10, 0, 0), la=(-55, -20, -17), lf=(-60, 0, 0), left_ribbon=(0, 0, 0),
          left_ribbon2=(0, 0, 0), head=(18, -14, 0))
    c.key(2.8, head=(8, 16, 0))
    c.key(3.2, la=(0, 0, 0), lf=(0, 0, 0), ra=(0, 0, 0), rf=(0, 0, 0), head=(0, 0, 0))
    c.key(3.8)


@clip("smooth_sash", "Smooths the sash", length=3.6, weight=1, require=ADULT, boost=SHY, mirror="free")
def _(c):
    # both hands run down the front of the sash; a quick look aside to see if anyone noticed
    top = dict(ra=(-30, -38, -20), rf=(-58, 0, 0), la=(-30, -38, -17), lf=(-62, 0, 0))
    bottom = dict(ra=(-10, -34, -20), rf=(-40, 0, 0), la=(-10, -34, -17), lf=(-44, 0, 0))
    c.key(0.5, head=(24, 0, 0), **top)
    c.key(1.1, sash=(4, 0, 0), **bottom)
    c.key(1.5, sash=(0, 0, 0), **top)
    c.key(2.1, sash=(4, 0, 0), **bottom)
    c.key(2.5, head=(12, 26, 0), sash=(0, 0, 0))
    c.key(3.0, head=(4, 0, 0), ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0))
    c.key(3.6)


@clip("hug_elbows", "Hugs the elbows", length=4.4, weight=1, require=ADULT, boost=SHY, mirror="free")
def _(c):
    # arms folded tight, knees together, a small sway and a sideways look
    c.key(0.7, head=(12, -16, 0), rl=(0, 0, -4), ll=(0, 0, -4), rs=(10, 0, 0), ls=(10, 0, 0), **CROSSED)
    c.key(1.7, root=(0, 0, 3), head=(14, -20, -4))
    c.key(2.7, root=(0, 0, -3), head=(10, -8, 4))
    c.key(3.4, root=(0, 0, 0), head=(12, -14, 0), **CROSSED)
    c.key(3.9, ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0),
          rs=(0, 0, 0), ls=(0, 0, 0))
    c.key(4.4)


# -- the Evensong, at dusk over the Veil Court -----------------------------------------------------------------------

EVENSONG = ["adult", "routine:evensong"]


@clip("evensong_sway", "Sways in the Evensong", length=6.0, weight=4, require=EVENSONG, mirror="free")
def _(c):
    # arms open to the sunset, swaying slowly side to side, the head a beat behind the body
    def pose(t):
        e = env(t, 0, 6.0, 1.0)
        s, lag = sn(t - 0.4, 3.0), sn(t - 0.4, 3.0, -0.12)
        return dict(ra=(-40 * e, 40 * e, (24 + 4 * s) * e), la=(-40 * e, 40 * e, (24 - 4 * s) * e),
                    rf=(20 * e, 0, 0), lf=(14 * e, 0, 0),
                    root=(-4 * e, 0, 7 * s * e), root_pos=(0, -0.6 * e, 0),
                    head=(-12 * e, 0, 8 * lag * e), hair=(12 * e, 0, -8 * lag * e),
                    right_veil=(0, 0, (14 - 6 * s) * e), left_veil=(0, 0, (14 + 6 * s) * e))
    sampled(c, 0, 6.0, pose, step=0.15)


@clip("evensong_high_note", "Sings with the head back", length=5.6, weight=4, require=EVENSONG)
def _(c):
    # a hand on the heart; the other hand rises with the long high note and the whole body lifts with it
    c.key(0.8, head=(-14, 0, 0), hair=(14, 0, 0), la=(-40, 10, 10), lf=(-10, 0, 0), **CHEST_R)
    c.key(2.6, head=(-30, 0, 4), hair=(30, 0, 0), la=(-150, 10, 4), lf=(20, 0, 0), root=(-6, 0, 0),
          root_pos=(0, -3, 0), rs=(-17, 0, 0), ls=(-14, 0, 0))
    c.wobble(2.6, 3.8, 6, "head", 1.5, base=(-30, 0, 4), axis=2)
    c.key(1.4, left_ribbon=(0, 0, 0), left_ribbon2=(0, 0, 0))
    c.key(2.4, **DROOP_L)
    c.key(3.9, **DROOP_L)
    c.key(4.6, left_ribbon=(0, 0, 0), left_ribbon2=(0, 0, 0))
    c.key(3.8, head=(-30, 0, 4), la=(-152, 12, 4), root_pos=(0, -3.2, 0), root=(-6, 0, 0))
    c.key(4.6, head=(-6, 0, 0), hair=(6, 0, 0), la=(-20, 0, 10), lf=(0, 0, 0), root=(0, 0, 0), root_pos=(0, 0, 0),
          rs=(0, 0, 0), ls=(0, 0, 0), **CHEST_R)
    c.key(5.1, ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), head=(0, 0, 0), hair=(0, 0, 0))
    c.key(5.6)


@clip("evensong_glide", "A slow turning glide", length=6.0, weight=4, require=EVENSONG, mirror="free")
def _(c):
    # one long slow turn in place, arms spread like wings, leaning into it, the veils trailing round
    glide = dict(ra=(-6, 0, 50), la=(-6, 0, 60), rf=(20, 0, 0), lf=(14, 0, 0), head=(-8, 0, -6),
                 right_veil=(20, 0, 25), left_veil=(20, 0, 35), **STRAIGHT_LEGS)
    c.key(0.8, **glide)
    c.key(5.0, **glide)
    full_turn(c, 0.5, 5.4, 1, extra=lambda t, a: (0, 0, -8 * math.sin(math.radians(a / 2))))
    c.key(5.6, ra=(0, 0, 0), la=(0, 0, 0), rf=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0), right_veil=(0, 0, 0),
          left_veil=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0))


# -- sheltering from a storm ----------------------------------------------------------------------------------------

SHELTER = ["adult", "routine:shelter"]


@clip("storm_huddle", "Huddles from the storm", length=5.6, weight=4, require=SHELTER, mirror="free")
def _(c):
    # curled small with arms wrapped round and the veils drawn in, shivering; a wary look up, and down again
    huddle = dict(rl=(-50, 0, 0), ll=(-55, 0, 0), rs=(60, 0, 0), ls=(65, 0, 0), right_veil=(-30, -20, -15),
                  left_veil=(-30, -20, -15), **CROSSED)
    c.key(0.8, head=(22, 0, 0), root=(8, 0, 0), **huddle)
    c.wobble(0.8, 2.6, 10, "root", 1.4, base=(8, 0, 0), axis=2)
    c.key(2.6, head=(22, 0, 0), root=(8, 0, 0))
    c.key(3.2, head=(-6, 14, 0), root=(4, 0, 0))
    c.key(3.8, head=(-4, -10, 0))
    c.key(4.3, head=(22, 0, 0), root=(8, 0, 0))
    c.wobble(4.3, 5.0, 10, "root", 1.2, base=(8, 0, 0), axis=2, decay=0.5)
    c.key(5.6)


@clip("thunder_flinch", "Flinches at thunder", length=4.6, weight=4, require=SHELTER)
def _(c):
    # crack! Arms fly up over the head, knees jerk up; a trembling wait; a peek; a hand on the pounding heart
    cover = dict(ra=(-135, -35, -20), rf=(-112, 0, 0), la=(-135, -35, -17), lf=(-118, 0, 0))
    c.key(0.5, head=(4, 0, 0))
    c.key(0.7, head=(26, 0, 0), root_pos=(0, -2, 0), rl=(-40, 0, 0), ll=(-40, 0, 0), rs=(50, 0, 0), ls=(50, 0, 0),
          root=(10, 0, 0), **cover, **DROOP_R, **DROOP_L)
    c.wobble(0.75, 2.0, 9, "head", 2.5, base=(26, 0, 0), axis=2)
    c.key(2.0, root_pos=(0, -0.5, 0), root=(8, 0, 0), rl=(-30, 0, 0), ll=(-30, 0, 0), rs=(40, 0, 0),
          ls=(40, 0, 0), **cover, **DROOP_R, **DROOP_L)
    c.key(3.0, **RIBBONS_REST)
    c.key(2.6, head=(-4, 18, 0), ra=(-100, -30, -20), la=(-120, -30, -17), root=(4, 0, 0))
    c.key(3.2, head=(6, 0, 0), la=(-10, 0, 0), lf=(0, 0, 0), root=(0, 0, 0), root_pos=(0, 0, 0), rl=(0, 0, 0),
          ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0), **CHEST_R)
    c.key(3.5, root_pos=(0, 0.6, 0))
    c.key(4.0, ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), head=(0, 0, 0), root_pos=(0, 0, 0))
    c.key(4.6)
