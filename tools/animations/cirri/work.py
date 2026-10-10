from kit import clip
import math

# The Cirri's trades, mimed in the air at their workplaces. Weights keep the trade visible among the everyday
# moments; at their workplace in working hours ("working") they come up far more often. The live hovering pose is
# under every clip (arms afloat about 20 degrees out with soft elbows): the poses below allow for it. While a clip
# plays, the model's own working gestures rest.

HIP = 13.0   # the pack's hip height: the root turns about it
MID = 7.0    # a grown-up's middle: leans turn about it
WORK = {"working": 3}


def job(name):
    return ["adult", "job:" + name]


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


def lean(c, t, angle, **pose):
    """Tip the whole body forward (+) or back (-) about its middle."""
    a = math.radians(angle)
    d = MID - HIP
    c.key(t, root=(angle, 0, 0), root_pos=(0, d - d * math.cos(a), -d * math.sin(a)), **pose)


# poses worked out on the live model (right side; mirror by swapping r/l)
CHEST_R = dict(ra=(-25, -45, -20), rf=(-80, 0, 0))
CHEST_L = dict(la=(-30, -45, -17), lf=(-88, 0, 0))
CUPPED = dict(ra=(-40, -35, -20), rf=(-50, 0, 0), la=(-40, -35, -17), lf=(-55, 0, 0))
EAR_R = dict(ra=(-95, 40, 0), rf=(-135, 0, 0))
DROOP_R = dict(right_ribbon=(120, 0, 0), right_ribbon2=(30, 0, 0))
DROOP_L = dict(left_ribbon=(120, 0, 0), left_ribbon2=(30, 0, 0))
RIBBONS_REST = dict(right_ribbon=(0, 0, 0), right_ribbon2=(0, 0, 0), left_ribbon=(0, 0, 0), left_ribbon2=(0, 0, 0))
ARMS_REST = dict(ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0))


# -- harpist: the wind harps of the Hall of Echoes -------------------------------------------------------------------

@clip("harp_pluck", "Plucks an air harp", length=5.0, weight=4, require=job("harpist"), boost=WORK)
def _(c):
    # the left hand steadies the harp's neck up high; the right picks out a tune at chest height, the head
    # leaning in to the strings and swaying with it
    c.key(0.6, la=(-100, 20, 0), lf=(-30, 0, 0), ra=(-50, -25, -20), rf=(-55, 0, 0), head=(6, 0, 10),
          hair=(-6, 0, 0))
    notes = [(-15, 0.9), (-5, 1.25), (-22, 1.6), (-10, 1.95), (0, 2.3), (-18, 2.8), (-8, 3.15), (-25, 3.5)]
    for yaw, t in notes:
        c.key(t, ra=(-52, yaw, -20), rf=(-62, 0, 0))
        c.key(t + 0.12, ra=(-48, yaw + 4, -20), rf=(-48, 0, 0))

    def sway(t):
        e = env(t, 0.6, 4.1, 0.5)
        return dict(head=(6 * e, 4 * sn(t, 2.8) * e, (10 + 4 * sn(t, 1.4)) * e), root=(0, 0, 2 * sn(t, 2.8) * e))
    sampled(c, 0.6, 4.1, sway, step=0.175)
    c.key(4.4, la=(-40, -10, -17), lf=(-20, 0, 0), ra=(-20, 0, -10), rf=(-20, 0, 0), hair=(0, 0, 0))
    c.key(5.0)


@clip("harp_tune", "Tunes the harp pegs", length=4.6, weight=3, require=job("harpist"), boost=WORK)
def _(c):
    # one hand up at the pegs giving a little twist, the other plucks the string; the head cocked to listen:
    # not quite... a touch more... there
    peg = dict(ra=(-140, -15, -20), rf=(-35, 0, 0))
    c.key(0.6, head=(-10, 10, -12), hair=(8, 0, 0), la=(-45, -25, -17), lf=(-50, 0, 0), **peg, **DROOP_R)
    for i, t in enumerate((0.9, 2.0)):
        c.wobble(t, t + 0.5, 6, "rf", 9, base=peg["rf"], axis=0)
        c.key(t + 0.65, la=(-48, -20, -17), lf=(-60, 0, 0))
        c.key(t + 0.8, la=(-44, -28, -17), lf=(-46, 0, 0), head=(-12, 14, -16))
        c.key(t + 1.05, head=(-8, 8, -10) if i == 0 else (-10, 10, -14))
    c.key(3.2, head=(2, 6, -6))
    c.key(3.45, head=(-6, 6, -6))
    c.key(3.6, **peg, **DROOP_R)
    c.key(4.1, ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0), hair=(0, 0, 0),
          **RIBBONS_REST)
    c.key(4.6)


@clip("harp_sweep", "Sweeps the harp strings", length=4.8, weight=3, require=job("harpist"), boost=WORK,
      mirror="free")
def _(c):
    # a glissando: both hands sweep down and across the strings, the body swaying into it; then again
    high = dict(ra=(-120, 25, 0), rf=(-30, 0, 0), la=(-105, -45, -17), lf=(-40, 0, 0))
    low = dict(ra=(-40, -35, -20), rf=(-40, 0, 0), la=(-30, 20, 10), lf=(-20, 0, 0))
    c.key(0.6, head=(-8, 14, 0), root=(0, 0, -4), **high)
    c.key(1.5, head=(10, -12, 6), root=(0, 0, 5), root_pos=(0, 0.6, 0), **low)
    c.key(2.1, head=(-6, 14, -2), root=(0, 0, -4), root_pos=(0, 0, 0), **high)
    c.key(3.0, head=(-14, -10, 8), root=(0, 0, 6), root_pos=(0, -0.6, 0), hair=(10, 0, 0), **low)
    # the last note rings: arms float open, the head back to hear it go
    c.key(3.6, ra=(-30, 20, 30), rf=(10, 0, 0), la=(-30, 20, 30), lf=(10, 0, 0), head=(-18, 0, 0), root=(0, 0, 0),
          root_pos=(0, -0.8, 0), hair=(16, 0, 0))
    c.key(4.3, head=(0, 0, 0), hair=(0, 0, 0), root_pos=(0, 0, 0), **ARMS_REST)
    c.key(4.8)


# -- weaver: the Loom House, combing cirrus at dawn ------------------------------------------------------------------

@clip("weave_comb", "Combs cirrus cloud", length=5.2, weight=4, require=job("weaver"), boost=WORK)
def _(c):
    # the left hand holds a hank of cloud up in front; the right draws the comb through it in long strokes,
    # from high above down past the hip
    hold = dict(la=(-75, -25, -17), lf=(-40, 0, 0))
    c.key(0.6, head=(-12, 0, 0), **hold)
    for t0 in (0.7, 2.3):
        c.key(t0 + 0.3, ra=(-160, -10, -20), rf=(10, 0, 0), head=(-20, 4, 0), **DROOP_R)
        c.key(t0 + 1.1, ra=(-50, 12, 0), rf=(0, 0, 0), head=(10, 6, 0), root=(4, 0, 0))
        c.key(t0 + 1.5, ra=(10, 20, 20), rf=(10, 0, 0), head=(14, 10, 0), root=(0, 0, 0), **RIBBONS_REST)
    c.key(4.3, ra=(0, 0, 4), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0))
    c.key(5.2)


@clip("weave_draw_thread", "Draws out a thread", length=4.8, weight=3, require=job("weaver"), boost=WORK)
def _(c):
    # pinched between the fingers, a fine thread of cloud is drawn out to the side, hand over hand, the eyes
    # following it all the way
    c.key(0.5, head=(14, 0, 0), **CUPPED)
    c.key(1.3, ra=(-78, 62, 8), rf=(20, 0, 0), head=(6, 30, 4))
    c.key(1.6, la=(-60, -70, -17), lf=(-10, 0, 0), head=(8, 26, 4))
    c.key(1.9, ra=(-40, -35, -20), rf=(-50, 0, 0), head=(12, 10, 0))
    c.key(2.7, ra=(-80, 66, 10), rf=(25, 0, 0), la=(-55, -40, -17), lf=(-30, 0, 0), head=(4, 36, 6),
          root=(0, 10, 0))
    c.key(3.2, head=(-4, 38, 8), root=(0, 12, 0))
    # it holds: a little tug to test it, and a pleased nod
    c.key(3.45, ra=(-76, 60, 8), rf=(15, 0, 0))
    c.key(3.6, ra=(-80, 66, 10), rf=(25, 0, 0), head=(4, 34, 6))
    c.key(4.2, head=(0, 0, 0), root=(0, 0, 0), **ARMS_REST)
    c.key(4.8)


@clip("weave_knot", "Ties off a knot", length=4.2, weight=3, require=job("weaver"), boost=WORK, mirror="free")
def _(c):
    # small busy fingers at chest height, the head bent close; then a quick tug apart to pull it tight
    close = dict(ra=(-48, -38, -20), rf=(-62, 0, 0), la=(-48, -38, -17), lf=(-66, 0, 0))
    c.key(0.5, head=(24, 0, 0), **close)
    c.wobble(0.6, 2.2, 3.5, "rf", 10, base=close["rf"], axis=0)
    c.wobble(0.6, 2.2, 3.5, "lf", 10, base=close["lf"], axis=0)
    c.wobble(0.6, 2.2, 1.5, "head", 4, base=(24, 0, 0), axis=2)
    c.key(2.4, ra=(-55, 30, 20), rf=(-20, 0, 0), la=(-55, 30, 20), lf=(-20, 0, 0), head=(10, 0, 0),
          root_pos=(0, -0.5, 0))
    c.key(2.6, ra=(-50, 22, 15), rf=(-26, 0, 0), la=(-50, 22, 15), lf=(-26, 0, 0), root_pos=(0, 0, 0))
    c.key(3.0, head=(16, 0, 0))
    c.key(3.3, head=(6, 0, 0))
    c.key(3.7, head=(0, 0, 0), **ARMS_REST)
    c.key(4.2)


# -- gardener: the Cloud Garden, its skywood trees and the koi pool -------------------------------------------------

@clip("garden_sprinkle", "Sprinkles water on the flowers", length=4.8, weight=4, require=job("gardener"),
      boost=WORK)
def _(c):
    # a bowl of dew on the left hip; the right hand dips and flicks the drops out, this way, that way, there
    bowl = dict(la=(-30, -30, -17), lf=(-70, 0, 0))
    dip = dict(ra=(-35, -40, -20), rf=(-75, 0, 0))
    c.key(0.5, head=(18, -6, 0), **bowl, **dip)
    for t, yaw, head in ((0.9, -10, -8), (1.8, 25, 18), (2.7, 50, 30)):
        c.key(t, ra=(-75, yaw, 0), rf=(15, 0, 0), head=(10, head, 0))
        c.key(t + 0.45, head=(18, head * 0.4, 0), **dip)
    c.key(3.6, head=(6, 10, 0))
    c.key(4.2, head=(0, 0, 0), **ARMS_REST)
    c.key(4.8)


@clip("garden_prune", "Prunes a skywood branch", length=5.0, weight=4, require=job("gardener"), boost=WORK)
def _(c):
    # the left hand holds a branch above; the right snips the straggly twigs; one clipping tossed away
    c.key(0.6, la=(-130, -10, -17), lf=(-25, 0, 0), ra=(-120, -25, -20), rf=(-40, 0, 0), head=(-22, 0, 0),
          hair=(18, 0, 0), **DROOP_R, **DROOP_L)
    for t in (0.95, 1.4, 2.2, 2.65):
        c.key(t, rf=(-55, 0, 0), ra=(-122, -25, -20))
        c.key(t + 0.15, rf=(-38, 0, 0), ra=(-118, -22, -20))
    c.key(1.8, head=(-24, 8, 0), ra=(-125, -10, -20))
    c.key(3.3, ra=(-90, 30, 20), rf=(-20, 0, 0), head=(-6, 20, 0))
    c.key(3.6, ra=(-60, 60, 40), rf=(20, 0, 0), head=(4, 34, 0), **RIBBONS_REST)
    c.key(4.3, head=(0, 0, 0), hair=(0, 0, 0), **ARMS_REST)
    c.key(5.0)


@clip("garden_koi_crumb", "Coaxes a koi with a crumb", length=5.6, weight=3, require=job("gardener"), boost=WORK)
def _(c):
    # leaning down over the pool with a crumb held out low, wiggling it; a koi nips - a start and a delighted bob
    lean(c, 0.8, 26, head=(28, 0, 0), hair=(-20, 0, 0), ra=(-40, -5, -20), rf=(20, 0, 0), right_veil=(-20, 0, 0),
         left_veil=(-20, 0, 0), **CHEST_L)
    c.wobble(1.0, 2.8, 2.5, "rf", 6, base=(20, 0, 0), axis=0)
    lean(c, 2.8, 28, head=(30, 0, 0), ra=(-44, -5, -20))
    c.key(3.05, ra=(-62, -12, -20), rf=(-45, 0, 0), head=(14, 0, 4))
    lean(c, 3.1, 14)
    c.key(3.5, head=(18, 0, -6), root_pos=(0, -1.0, -0.2))
    c.key(3.8, head=(22, 0, 6))
    lean(c, 4.4, 0, head=(0, 0, 0), hair=(0, 0, 0), right_veil=(0, 0, 0), left_veil=(0, 0, 0), **ARMS_REST)
    c.key(5.6)


# -- bellkeeper: the Bell Pagoda, dawn and dusk and before storms ---------------------------------------------------

@clip("bell_haul", "Hauls the bell rope", length=5.2, weight=5, require=job("bellkeeper"), boost=WORK,
      mirror="free")
def _(c):
    # hand over hand on a rope from above, the whole body dipping into each pull
    up_r = dict(ra=(-165, -5, -20), rf=(29, 0, 0), **DROOP_R)
    down_r = dict(ra=(-40, -25, -20), rf=(-85, 0, 0), right_ribbon=(0, 0, 0), right_ribbon2=(0, 0, 0))
    up_l = dict(la=(-165, -5, -17), lf=(20, 0, 0), **DROOP_L)
    down_l = dict(la=(-40, -25, -17), lf=(-90, 0, 0), left_ribbon=(0, 0, 0), left_ribbon2=(0, 0, 0))
    c.key(0.5, head=(-20, 0, 0), hair=(16, 0, 0), **up_r, **down_l)
    t = 0.5
    for i in range(4):
        a, b = (down_r, up_l) if i % 2 == 0 else (up_r, down_l)
        c.key(t + 0.55, root_pos=(0, 1.4, 0), head=(-10, 0, 0), **a, **b)
        c.key(t + 0.9, root_pos=(0, 0.2, 0), head=(-18, 0, 0))
        t += 0.9
    c.key(4.2, root_pos=(0, 0, 0), head=(-14, 0, 0))
    c.key(4.7, head=(0, 0, 0), hair=(0, 0, 0), **ARMS_REST, **RIBBONS_REST)
    c.key(5.2)


@clip("bell_listen", "Listens for the bell's note", length=4.8, weight=3, require=job("bellkeeper"), boost=WORK)
def _(c):
    # a hand cupped to the ear, head tipped and eyes shut, nodding along as the note hums away; true, good
    c.key(0.7, head=(-8, 10, -14), hair=(8, 0, 0), **EAR_R)
    c.key(1.6, head=(-10, 12, -18))
    c.key(2.2, head=(-4, 12, -16))
    c.key(2.6, head=(-10, 12, -18))
    c.key(3.0, head=(-4, 12, -16))
    c.key(3.5, head=(4, 0, 0), hair=(0, 0, 0), **CHEST_R)
    c.key(3.8, head=(10, 0, 0))
    c.key(4.3, head=(0, 0, 0), ra=(0, 0, 0), rf=(0, 0, 0))
    c.key(4.8)


# -- lamplighter: the Lantern Spire and the sky lanterns on the bridges ---------------------------------------------

@clip("lamp_raise_pole", "Raises the lighting pole", length=5.0, weight=4, require=job("lamplighter"), boost=WORK,
      mirror="free")
def _(c):
    # a long pole gripped in both hands, lifted up and up to a high lantern, a careful poke or two, and down
    grip = dict(ra=(-60, -20, -20), rf=(-60, 0, 0), la=(-90, -25, -17), lf=(-30, 0, 0))
    c.key(0.6, head=(-6, 0, 0), **grip)
    c.key(1.5, ra=(-140, -15, -20), rf=(-30, 0, 0), la=(-170, -10, -17), lf=(15, 0, 0), head=(-30, 0, 0),
          hair=(24, 0, 0), root_pos=(0, -1.5, 0), **DROOP_R, **DROOP_L)
    for t in (2.0, 2.6):
        c.key(t, ra=(-150, -15, -20), la=(-175, -10, -17), root_pos=(0, -2.2, -0.6))
        c.key(t + 0.3, ra=(-140, -15, -20), la=(-170, -10, -17), root_pos=(0, -1.5, 0))
    c.key(3.4, head=(-24, 0, 0))
    c.key(4.2, head=(0, 0, 0), hair=(0, 0, 0), root_pos=(0, 0, 0), **ARMS_REST, **RIBBONS_REST)
    c.key(5.0)


@clip("lamp_trim_wick", "Trims a wick", length=4.6, weight=3, require=job("lamplighter"), boost=WORK)
def _(c):
    # the lantern held up close in the left hand, the right snipping the wick; then fingers blown on: hot!
    c.key(0.6, la=(-70, -30, -17), lf=(-60, 0, 0), ra=(-60, -38, -20), rf=(-70, 0, 0), head=(18, 0, 0))
    c.wobble(0.7, 2.0, 4, "rf", 8, base=(-70, 0, 0), axis=0)
    c.key(2.0, head=(16, 0, 4))
    c.key(2.3, ra=(-62, -45, -20), rf=(-100, 0, 0), head=(4, 0, 0))
    c.wobble(2.35, 3.1, 5, "ra", 4, base=(-62, -45, -20), axis=1)
    c.key(3.1, head=(2, 0, 0))
    c.wobble(3.1, 3.6, 6, "head", 6, base=(2, 0, 0), axis=1, decay=0.4)
    c.key(4.1, head=(0, 0, 0), **ARMS_REST)
    c.key(4.6)


@clip("lamp_shield_flame", "Shields a flame from the wind", length=5.0, weight=3, require=job("lamplighter"),
      boost=WORK, mirror="free")
def _(c):
    # cupped hands round a new flame, the body curled over it and turned from the wind; a gust; it holds
    cup = dict(ra=(-55, -40, -20), rf=(-55, 0, 0), la=(-55, -40, -17), lf=(-60, 0, 0))
    c.key(0.6, head=(22, 0, 0), **cup)
    c.key(1.3, root=(10, -22, 0), head=(26, 0, 0), right_veil=(-10, 0, -10), left_veil=(-10, 0, -10), **cup)
    c.wobble(1.8, 2.8, 6, "root", 2, base=(10, -22, 0), axis=2, decay=0.4)
    c.key(2.8, root=(12, -24, 0), head=(28, 0, 0))
    c.key(3.4, root=(4, -10, 0), head=(14, 0, 0), ra=(-60, -30, -20), la=(-60, -30, -17))
    c.key(3.8, head=(20, 0, 4))
    c.key(4.4, root=(0, 0, 0), head=(0, 0, 0), right_veil=(0, 0, 0), left_veil=(0, 0, 0), **ARMS_REST)
    c.key(5.0)


# -- skymerchant: the Market Pavilion and its walkers ----------------------------------------------------------------

@clip("merchant_present", "Presents wares on both palms", length=4.4, weight=4, require=job("skymerchant"),
      boost=WORK, mirror="free")
def _(c):
    # both palms held out with something lovely on them, a little bow, then a sweep of the arm over the stall
    offer = dict(ra=(-55, -5, -12), rf=(-10, 0, 0), la=(-55, -5, -10), lf=(-15, 0, 0))
    c.key(0.6, head=(6, 0, 8), **offer)
    lean(c, 1.2, 10, head=(12, 0, 10))
    lean(c, 1.9, 0, head=(-2, 0, 6))
    c.key(2.5, ra=(-62, 55, -2), rf=(20, 0, 0), la=(-20, -10, -10), lf=(-20, 0, 0), head=(0, 30, 0),
          root=(0, 12, 0))
    c.key(3.2, ra=(-55, 68, 4), head=(2, 24, 6), root=(0, 8, 0))
    c.key(3.8, head=(0, 0, 0), root=(0, 0, 0), **ARMS_REST)
    c.key(4.4)


@clip("merchant_count", "Counts on the fingers", length=4.6, weight=3, require=job("skymerchant"), boost=WORK)
def _(c):
    # the right forefinger taps off the left hand's fingers one by one, a nod for each; then a raised finger:
    # and that is the price
    c.key(0.5, la=(-50, -30, -17), lf=(-50, 0, 0), ra=(-45, -40, -20), rf=(-60, 0, 0), head=(20, 0, 0))
    for i, yaw in enumerate((-46, -40, -34, -28)):
        t = 0.8 + i * 0.5
        c.key(t, ra=(-48, yaw, -20), rf=(-66, 0, 0), head=(22, 0, 2 if i % 2 else -2))
        c.key(t + 0.2, ra=(-44, yaw, -20), rf=(-58, 0, 0), head=(18, 0, 0))
    c.key(3.1, ra=(-110, -20, -20), rf=(-50, 0, 0), la=(-20, -10, -10), lf=(-20, 0, 0), head=(-2, 0, 6),
          **DROOP_R)
    c.key(3.6, ra=(-108, -18, -20), head=(-4, 0, 8))
    c.key(4.1, head=(0, 0, 0), **ARMS_REST, **RIBBONS_REST)
    c.key(4.6)


@clip("merchant_shrug", "A haggler's shrug", length=3.6, weight=3, require=job("skymerchant"), boost=WORK,
      mirror="free")
def _(c):
    # palms out, head on one side: what can I do, it is a fair price; the arms drop with a sigh
    # (elbows in at the sides, the upper arms turned out so the forearms open outward, palms up)
    c.key(0.5, ra=(-15, 30, -6), rf=(-40, 0, 0), la=(-15, 30, -4), lf=(-45, 0, 0), head=(0, 0, 4))
    c.key(0.9, ra=(-22, 50, -2), rf=(-55, 0, 0), la=(-22, 50, 0), lf=(-62, 0, 0), head=(-4, 0, 16),
          root_pos=(0, -1, 0))
    c.key(1.8, ra=(-22, 52, 0), la=(-22, 52, 2), head=(-4, 6, 18))
    c.key(2.3, ra=(4, 0, 4), rf=(0, 0, 0), la=(4, 0, 4), lf=(0, 0, 0), head=(6, 0, 4), root_pos=(0, 0.8, 0))
    c.key(2.9, head=(0, 0, 0), root_pos=(0, 0, 0), ra=(0, 0, 0), la=(0, 0, 0))
    c.key(3.6)


# -- windkeeper: the Lift Dock and its Wind Stone far below ---------------------------------------------------------

@clip("wind_read", "Reads the wind", length=5.2, weight=4, require=job("windkeeper"), boost=WORK)
def _(c):
    # a hand held high with the fingers spread, turning slowly to feel where the wind is coming from; found
    # it: a point that way, and a knowing nod
    up = dict(ra=(-160, 0, -10), rf=(29, 0, 0), **DROOP_R)
    c.key(0.7, head=(-16, 0, -6), hair=(12, 0, 0), **up)
    c.key(1.7, root=(0, -20, 0), head=(-18, -6, -8))
    c.key(2.8, root=(0, 18, 0), head=(-18, 8, -6))
    c.key(3.2, root=(0, 22, 0), head=(-14, 10, 0))
    c.key(3.6, ra=(-95, 35, 0), rf=(29, 0, 0), head=(-4, 20, 0), root=(0, 18, 0), **RIBBONS_REST)
    c.key(3.9, head=(6, 20, 0))
    c.key(4.6, head=(0, 0, 0), hair=(0, 0, 0), root=(0, 0, 0), ra=(0, 0, 0), rf=(0, 0, 0))
    c.key(5.2)


@clip("wind_beckon", "Beckons a walker up", length=4.6, weight=4, require=job("windkeeper"), boost=WORK)
def _(c):
    # peering down the shaft at a walker far below: come up, come up! A cheery scoop of the arm, twice
    lean(c, 0.7, 14, head=(30, 0, 0), hair=(-12, 0, 0), ra=(-45, 0, -20), rf=(29, 0, 0))
    for t in (1.0, 2.0):
        c.key(t + 0.4, ra=(-110, -10, -20), rf=(-80, 0, 0))
        c.key(t + 0.9, ra=(-48, 0, -20), rf=(25, 0, 0))
    c.key(3.2, head=(24, 0, 6))
    c.key(3.5, head=(30, 0, -4))
    lean(c, 4.1, 0, head=(0, 0, 0), hair=(0, 0, 0), ra=(0, 0, 0), rf=(0, 0, 0))
    c.key(4.6)


@clip("wind_guide", "Guides a walker up on the wind", length=5.2, weight=3, require=job("windkeeper"), boost=WORK,
      mirror="free")
def _(c):
    # palms down over the shaft, then a slow, steady lift of both hands as the wind carries someone up; the eyes
    # follow them from far below to right in front
    low = dict(ra=(-50, -12, -20), rf=(10, 0, 0), la=(-50, -12, -17), lf=(5, 0, 0))
    c.key(0.7, head=(30, 0, 0), **low)
    c.key(1.3, ra=(-54, -12, -20), la=(-54, -12, -17), head=(30, 0, 0))
    c.key(3.6, ra=(-100, -10, -20), rf=(-5, 0, 0), la=(-100, -10, -17), lf=(-10, 0, 0), head=(-4, 0, 0),
          root_pos=(0, -1.2, 0))
    c.key(4.1, ra=(-90, 10, 0), la=(-90, 10, 0), head=(-2, 0, 6), root_pos=(0, -1, 0))
    c.key(4.7, head=(0, 0, 0), root_pos=(0, 0, 0), **ARMS_REST)
    c.key(5.2)
