"""Reactions: gifts, friendship, apologies and blows. Being airborne, a Cirri's joy is a loop-the-loop or a spin
with the veils flying, its thanks a bow in the air, its displeasure a turned back and a flick of the veils, and a
blow knocks it tumbling.

Full turns use the body part (it carries everything, about the hips), not root: the director scales a reaction's
root (and legs) down while the Cirri is moving, which would show the unseen snap from 360 back to 0 (and a hurt
Cirri always flies off). Small root turns and root_pos lifts are fine there: they only shrink."""
import math

from kit import clip


def bowed(p, legs=1.0, head=0.0, veils=1.0):
    """The body tipped forward p degrees at the hips, with the legs, veils and hair kept hanging."""
    return dict(body=(p, 0, 0), rl=(-p * legs, 0, 0), ll=(-p * legs, 0, 0),
                right_veil=(-p * veils, 0, 0), left_veil=(-p * veils, 0, 0), hair=(-(p + head) * 0.8, 0, 0))


def ease(s):
    return (1 - math.cos(math.pi * s)) / 2


def turn_over(c, t0, t1, deg, h=5.0, rise=0.0, loop=0.0, steps=16, shape=ease):
    """The whole Cirri turned head over heels, deg (+-360) between t0 and t1, about a point h pixels above the
    hips, rising by rise halfway and (loop > 0) travelling a circle of that radius with the head leading; then the
    turn snaps back to 0 unseen (360 is the same pose)."""
    for i in range(steps + 1):
        s = i / steps
        e = shape(s)
        r = math.radians(deg * e)
        phi = 2 * math.pi * e
        y = -h + h * math.cos(r) - rise * math.sin(math.pi * e) - loop * math.sin(phi)
        z = h * math.sin(r) + loop * (1 - math.cos(phi)) * (1 if deg < 0 else -1)
        c.key(t0 + (t1 - t0) * s, body=(deg * e, 0, 0), root_pos=(0, y, z))
    c.key(t1 + 0.0001, body=(0, 0, 0), root_pos=(0, 0, 0))


def spin(c, t0, t1, deg=360, rise=0.0, steps=10):
    """A turn about the vertical (body yaw), rising by rise halfway, snapping back to 0 unseen at the end."""
    for i in range(steps + 1):
        s = i / steps
        e = ease(s)
        c.key(t0 + (t1 - t0) * s, body=(0, deg * e, 0), root_pos=(0, -rise * math.sin(math.pi * e), 0))
    c.key(t1 + 0.0001, body=(0, 0, 0), root_pos=(0, 0, 0))


def sampled(c, t0, t1, fn, step=0.1):
    n = max(2, round((t1 - t0) / step))
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        c.key(t, **fn(t))


HEART = dict(ra=(-22, -38, -18), rf=(-78, 0, 0))
FOLDED = dict(ra=(-30, -44, -20), rf=(-92, 0, 0), la=(-28, -46, -17), lf=(-95, 0, 0))
PRESSED = dict(ra=(-34, -46, -18), rf=(-96, 0, 0), la=(-34, -46, -18), lf=(-96, 0, 0))
GUARD = dict(ra=(-100, -36, -14), rf=(-70, 0, 0), la=(-96, -36, -14), lf=(-74, 0, 0))


# -- happy: a gift they love, a new level of friendship ---------------------------------------------------------

@clip("happy_loop", "A loop-the-loop with the arms flung out", trigger="happy", length=3.6, weight=3,
      require=["adult"], blend=(.2, .35), mirror="free")
def _(c):
    c.key(0.3, root_pos=(0, 0.8, 0), ra=(16, 0, 4), la=(16, 0, 4), rl=(-14, 0, 0), ll=(-14, 0, 0), rs=(26, 0, 0),
          ls=(26, 0, 0), head=(8, 0, 0))
    fling = dict(ra=(-20, 0, 72), la=(-20, 0, 72), rf=(12, 0, 0), lf=(12, 0, 0), rl=(-4, 0, 0), ll=(-4, 0, 0),
                 rs=(-16, 0, 0), ls=(-16, 0, 0), head=(-14, 0, 0), right_veil=(36, 0, 26), left_veil=(36, 0, 26),
                 right_veil2=(-8, 0, 0), left_veil2=(-8, 0, 0), hair=(20, 0, 0), sash=(-20, 0, 0))
    c.key(0.6, **fling)
    turn_over(c, 0.6, 2.1, -360, h=5, rise=1.5, loop=3.5)
    c.key(2.0, **fling)
    # out of the loop into a V of the arms, a happy tilt of the head
    c.key(2.4, ra=(-10, 0, 128), la=(-10, 0, 128), rf=(10, 0, 0), lf=(10, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0),
          rs=(0, 0, 0), ls=(0, 0, 0), head=(-10, 0, 8), right_veil=(14, 0, 18), left_veil=(14, 0, 18),
          right_veil2=(0, 0, 0), left_veil2=(0, 0, 0), hair=(0, 0, 0), sash=(0, 0, 0))
    c.key(2.75, head=(-10, 0, -6), ra=(-10, 0, 138), la=(-10, 0, 118))
    c.key(3.15, ra=(0, 0, 8), la=(0, 0, 8), rf=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0), right_veil=(0, 0, 0),
          left_veil=(0, 0, 0))
    c.key(3.6)


@clip("happy_spin", "Spins with the veils flying", trigger="happy", length=3.2, weight=2, require=["adult"],
      mirror="free")
def _(c):
    c.key(0.3, ra=(-10, 0, 40), la=(-10, 0, 40), head=(-6, 0, 0))
    out = dict(ra=(-10, 0, 76), la=(-10, 0, 76), rf=(12, 0, 0), lf=(12, 0, 0), head=(-12, 0, 0),
               right_veil=(26, 0, 56), left_veil=(26, 0, 56), right_veil2=(-14, 0, 0), left_veil2=(-14, 0, 0),
               right_veil3=(-8, 0, 0), left_veil3=(-8, 0, 0), hair=(40, 0, 0), sash=(-36, 0, 0),
               rl=(0, 0, 10), ll=(0, 0, 10))
    c.key(0.6, **out)
    spin(c, 0.6, 2.0, rise=2.2)
    c.key(1.9, **out)
    # a dizzy, happy wobble to a stop
    c.key(2.3, ra=(-10, 0, 34), la=(-10, 0, 34), rf=(0, 0, 0), lf=(0, 0, 0), right_veil=(6, 0, 10),
          left_veil=(6, 0, 10), right_veil2=(4, 0, 0), left_veil2=(4, 0, 0), right_veil3=(0, 0, 0),
          left_veil3=(0, 0, 0), hair=(-6, 0, 0), sash=(6, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0))
    c.wobble(2.05, 2.85, 3, "head", 9, base=(-4, 0, 0), axis=2, decay=0.5)
    c.key(2.85, ra=(0, 0, 0), la=(0, 0, 0), right_veil=(0, 0, 0), left_veil=(0, 0, 0), right_veil2=(0, 0, 0),
          left_veil2=(0, 0, 0), hair=(0, 0, 0), sash=(0, 0, 0))
    c.key(3.2)


@clip("happy_clasp_rise", "Hands clasped to the chest and a rise", trigger="happy", length=3.4, weight=3,
      require=["adult"])
def _(c):
    clasp = dict(ra=(-30, -46, -18), rf=(-90, 0, 0), la=(-30, -46, -18), lf=(-90, 0, 0))
    c.key(0.4, head=(-4, 0, 10), ra_pos=(0, -0.6, 0), la_pos=(0, -0.6, 0), **clasp)
    # up on the joy of it, toes pointed, the veils lifting, eyes to the sky
    c.key(1.6, root_pos=(0, -3.5, 0), head=(-14, 0, 6), hair=(12, 0, 0), rl=(4, 0, 0), ll=(4, 0, 0),
          rs=(-14, 0, 0), ls=(-14, 0, 0), right_veil=(18, 0, 20), left_veil=(18, 0, 20), right_veil2=(-10, 0, 0),
          left_veil2=(-10, 0, 0), **clasp)
    c.wave(0.6, 2.2, 0.8, "body", 4, axis=2)
    # and lets it go: the hands open out from the heart
    c.key(2.2, ra=(-44, 30, 20), rf=(-20, 0, 0), la=(-44, 30, 20), lf=(-20, 0, 0), head=(-10, 0, 0),
          root_pos=(0, -3.0, 0), ra_pos=(0, 0, 0), la_pos=(0, 0, 0))
    c.key(2.8, ra=(-6, 0, 6), rf=(-4, 0, 0), la=(-6, 0, 6), lf=(-4, 0, 0), head=(2, 0, 0), root_pos=(0, 0, 0),
          hair=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0), right_veil=(0, 0, 0),
          left_veil=(0, 0, 0), right_veil2=(0, 0, 0), left_veil2=(0, 0, 0))
    c.key(3.4)


@clip("happy_child_double_flip", "A double somersault", trigger="happy", length=3.0, weight=3,
      require=["child"], mirror="free")
def _(c):
    tuck = dict(ra=(-50, -10, 10), la=(-50, -10, 10), rf=(-60, 0, 0), lf=(-60, 0, 0), rl=(-80, 0, 0),
                ll=(-80, 0, 0), rs=(100, 0, 0), ls=(100, 0, 0), head=(14, 0, 0))
    c.key(0.25, root_pos=(0, 0.6, 0), head=(-6, 0, 0), rl=(-10, 0, 0), ll=(-10, 0, 0), rs=(20, 0, 0), ls=(20, 0, 0))
    c.key(0.45, **tuck)
    # twice round: no turn may pass 400 degrees, so the body turns 360 twice, snapping back to 0 unseen at the
    # seam (keys are dense there so the seam barely checks the turn); root_pos keeps the child's middle (4.5 px
    # above the hips) in place on a little hop
    t0, t1, n, h = 0.45, 1.6, 36, 4.5
    for i in range(n + 1):
        s = i / n
        e = ease(s)
        ang = 720 * e
        r = math.radians(ang)
        t = t0 + (t1 - t0) * s
        pos = (0, -h + h * math.cos(r) - 2.5 * math.sin(math.pi * e), h * math.sin(r))
        c.key(t, body=(ang if i <= n // 2 else ang - 360, 0, 0), root_pos=pos)
        if i == n // 2:
            c.key(t + 0.0001, body=(0, 0, 0))
    c.key(t1 + 0.0001, body=(0, 0, 0), root_pos=(0, 0, 0))
    c.key(1.5, **tuck)
    c.key(1.85, ra=(-10, 0, 150), la=(-10, 0, 150), rf=(10, 0, 0), lf=(10, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0),
          rs=(0, 0, 0), ls=(0, 0, 0), head=(-12, 0, 0))
    c.key(2.2, head=(-10, 0, 8))
    c.key(2.5, head=(-8, 0, -6), ra=(-10, 0, 120), la=(-10, 0, 120))
    c.key(2.75, ra=(0, 0, 6), la=(0, 0, 6), rf=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0))
    c.key(3.0)


@clip("happy_child_clap", "Claps and bounces", trigger="happy", length=2.8, weight=2, require=["child"],
      mirror="free")
def _(c):
    apart = dict(ra=(-60, 20, -6), rf=(-30, 0, 0), la=(-60, 20, -6), lf=(-30, 0, 0))
    together = dict(ra=(-62, -24, -14), rf=(-40, 0, 0), la=(-62, -24, -14), lf=(-40, 0, 0))
    c.key(0.3, head=(-8, 0, 0), **apart)
    c.cycle(0.3, 2.1, 0.36, apart, together, end_on="a")
    c.cycle(0.3, 2.1, 0.72, dict(root_pos=(0, 0.2, 0), rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0),
                                 head=(-8, 0, -6)),
            dict(root_pos=(0, -1.8, 0), rl=(-30, 0, 0), ll=(-30, 0, 0), rs=(50, 0, 0), ls=(50, 0, 0),
                 head=(-10, 0, 6)))
    c.key(2.45, ra=(0, 0, 4), rf=(0, 0, 0), la=(0, 0, 4), lf=(0, 0, 0), root_pos=(0, 0, 0), head=(0, 0, 0),
          rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0))
    c.key(2.8)


# -- thanks: a gift they like or don't mind ---------------------------------------------------------------------

@clip("thanks_receive", "Receives it with both hands and draws it to the chest", trigger="thanks", length=3.2,
      weight=3, require=["adult"])
def _(c):
    cup = dict(ra=(-46, -16, -16), rf=(-40, 0, 0), la=(-46, -16, -16), lf=(-40, 0, 0))
    c.key(0.45, head=(16, 0, 0), **cup, **bowed(4, legs=0.6))
    c.key(0.7, ra=(-48, -16, -16), la=(-48, -16, -16))
    c.key(1.3, ra=(-28, -42, -18), rf=(-88, 0, 0), la=(-28, -42, -18), lf=(-88, 0, 0), head=(14, 0, 4),
          root_pos=(0, -0.8, 0), **bowed(8, legs=0.6))
    c.key(1.8, head=(4, 0, 8), root_pos=(0, -1.2, 0), **bowed(0))
    c.key(2.4, ra=(-14, -16, -6), rf=(-40, 0, 0), la=(-14, -16, -6), lf=(-40, 0, 0), head=(0, 0, 4),
          root_pos=(0, -0.4, 0))
    c.key(3.2)


@clip("thanks_bow", "A bow of thanks with the hands pressed together", trigger="thanks", length=3.0, weight=2,
      require=["adult"])
def _(c):
    c.key(0.4, head=(4, 0, 0), **PRESSED)
    c.key(1.0, head=(14, 0, 0), **PRESSED, **bowed(20, head=14))
    c.key(1.5, head=(15, 0, 0), **PRESSED, **bowed(21, head=15))
    c.key(2.1, head=(-2, 0, 6), **PRESSED, **bowed(0))
    c.key(2.5, ra=(-6, 0, 0), rf=(-10, 0, 0), la=(-6, 0, 0), lf=(-10, 0, 0), head=(0, 0, 2))
    c.key(3.0)


@clip("thanks_heart_nods", "A hand to the heart and two nods", trigger="thanks", length=2.8, weight=2)
def _(c):
    c.key(0.35, head=(2, 0, 4), **HEART)
    for t in (0.65, 1.2):
        c.key(t, head=(13, 0, 4), hair=(-10, 0, 0))
        c.key(t + 0.3, head=(0, 0, 4), hair=(0, 0, 0))
    c.key(1.9, head=(0, 0, 6), ra=(-20, -30, -14), rf=(-60, 0, 0))
    c.key(2.8)


@clip("thanks_child_hug", "Hugs it close and wiggles", trigger="thanks", length=2.8, weight=3,
      require=["child"], mirror="free")
def _(c):
    hug = dict(ra=(-34, -48, -18), rf=(-100, 0, 0), la=(-34, -48, -18), lf=(-100, 0, 0))
    c.key(0.4, head=(8, 0, 8), **hug)
    c.wave(0.5, 2.1, 0.55, "body", 7, axis=2)
    c.wave(0.5, 2.1, 0.55, "head", 8, base=(8, 0, 4), axis=2, phase=0.5)
    c.key(1.1, root_pos=(0, -1.2, 0), rl=(-20, 0, 0), ll=(-20, 0, 0), rs=(30, 0, 0), ls=(30, 0, 0))
    c.key(1.6, root_pos=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0))
    c.key(2.1, **hug)
    c.key(2.4, ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0))
    c.key(2.8)


@clip("thanks_child_bob", "A quick bob of thanks", trigger="thanks", length=2.2, weight=2, require=["child"])
def _(c):
    c.key(0.3, head=(4, 0, 0), **PRESSED)
    c.key(0.6, head=(16, 0, 0), **PRESSED, **bowed(22, head=16))
    c.key(1.0, head=(-8, 0, 6), root_pos=(0, -1.6, 0),
          **{**bowed(0), "rl": (-20, 0, 0), "ll": (-20, 0, 0)}, rs=(30, 0, 0), ls=(30, 0, 0))
    c.key(1.35, root_pos=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0), head=(0, 0, 4))
    c.key(1.8, ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0))
    c.key(2.2)


# -- decline: a gift they dislike, a sorry not yet accepted -----------------------------------------------------

@clip("decline_palm", "A raised palm and a turned head", trigger="decline", length=2.8, weight=3,
      require=["adult"])
def _(c):
    c.key(0.35, ra=(-48, 6, -14), rf=(-62, 0, 0), head=(4, -16, 0), root=(0, -6, 0), root_pos=(0, 0, 0.8),
          right_veil=(-4, 0, -8), left_veil=(-4, 0, -8))
    c.key(0.55, ra=(-52, 6, -14), rf=(-58, 0, 0))
    c.key(0.8, head=(6, -24, 0))
    c.key(1.05, head=(6, -12, 0))
    c.key(1.3, head=(6, -22, 0))
    c.key(1.9, ra=(-30, 4, -8), rf=(-40, 0, 0), head=(2, -8, 0), root=(0, -3, 0), root_pos=(0, 0, 0.4),
          right_veil=(0, 0, 0), left_veil=(0, 0, 0))
    c.key(2.8)


@clip("decline_veils_close", "Shakes the head politely with the veils drawn close", trigger="decline",
      length=3.2, weight=2, require=["adult"])
def _(c):
    # the hands draw the stole close at the shoulders and the veils fold in round them
    wrap = dict(ra=(-30, -50, -18), rf=(-104, 0, 0), la=(-28, -52, -17), lf=(-100, 0, 0))
    veils = dict(right_veil=(-6, -24, -22), left_veil=(-6, -24, -22), right_veil2=(4, 0, 0), left_veil2=(4, 0, 0))
    c.key(0.5, head=(6, 0, 0), root_pos=(0, 0, 0.5), **wrap, **veils)
    c.key(0.85, head=(8, -12, 0))
    c.key(1.2, head=(8, 12, 0))
    c.key(1.55, head=(8, -10, 0))
    c.key(1.9, head=(8, 6, 0))
    # a small, courteous nod: thank you, but no
    c.key(2.2, head=(13, 0, 2), **wrap, **veils)
    c.key(2.7, ra=(-10, -10, -4), rf=(-20, 0, 0), la=(-10, -10, -4), lf=(-20, 0, 0), head=(2, 0, 0),
          right_veil=(0, 0, 0), left_veil=(0, 0, 0), right_veil2=(0, 0, 0), left_veil2=(0, 0, 0),
          root_pos=(0, 0, 0))
    c.key(3.2)


@clip("decline_child_pout", "Crossed arms and a pout", trigger="decline", length=2.8, weight=3,
      require=["child"])
def _(c):
    c.key(0.4, head=(-10, -8, 0), **FOLDED)
    # chin up, a shake of the head, and one stubborn kick
    c.key(0.7, head=(-12, 12, 0), rl=(-24, 0, 0), rs=(34, 0, 0))
    c.key(1.0, head=(-12, -12, 0), rl=(6, 0, 0), rs=(0, 0, 0))
    c.key(1.3, head=(-12, 10, 0))
    c.key(1.6, head=(-12, -8, 4))
    c.key(2.1, head=(-10, -10, 6), **FOLDED)
    c.key(2.5, ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0), rl=(0, 0, 0))
    c.key(2.8)


# -- pleased: a sorry accepted ----------------------------------------------------------------------------------

@clip("pleased_sigh", "A relieved sigh as the shoulders drop", trigger="pleased", length=3.2, weight=3,
      require=["adult"])
def _(c):
    c.key(0.6, ra_pos=(0, -0.8, 0), la_pos=(0, -0.8, 0), head=(-8, 0, 0), body=(-3, 0, 0), rl=(3, 0, 0),
          ll=(3, 0, 0), right_veil=(8, 0, 8), left_veil=(8, 0, 8), root_pos=(0, -0.6, 0))
    # and out: everything settles a little lower and softer
    c.key(1.4, ra_pos=(0, 0.6, 0), la_pos=(0, 0.6, 0), head=(10, 0, 6), body=(3, 0, 0), rl=(-3, 0, 0),
          ll=(-3, 0, 0), ra=(4, 0, -10), la=(4, 0, -10), rf=(10, 0, 0), lf=(10, 0, 0), right_veil=(-2, 0, -4),
          left_veil=(-2, 0, -4), root_pos=(0, 0.8, 0))
    c.key(2.0, head=(4, 0, 8))
    c.key(2.6, ra_pos=(0, 0, 0), la_pos=(0, 0, 0), head=(0, 0, 2), body=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0),
          ra=(0, 0, 0), la=(0, 0, 0), rf=(0, 0, 0), lf=(0, 0, 0), right_veil=(0, 0, 0), left_veil=(0, 0, 0),
          root_pos=(0, 0, 0))
    c.key(3.2)


@clip("pleased_warm_nod", "A warm nod and open hands", trigger="pleased", length=3.0, weight=2,
      require=["adult"], mirror="free")
def _(c):
    open_ = dict(ra=(-30, 28, 4), rf=(-40, 0, 0), la=(-30, 28, 4), lf=(-40, 0, 0))
    c.key(0.4, head=(2, 0, 6))
    c.key(0.8, head=(13, 0, 6), root_pos=(0, -0.4, 0), **open_)
    c.key(1.25, head=(2, 0, 8), root_pos=(0, -1.0, 0))
    c.key(1.9, head=(4, 0, 8), root_pos=(0, -1.0, 0), **open_)
    c.key(2.5, ra=(-4, 0, 0), rf=(-6, 0, 0), la=(-4, 0, 0), lf=(-6, 0, 0), head=(0, 0, 2), root_pos=(0, 0, 0))
    c.key(3.0)


@clip("pleased_child_wiggle", "A relieved little wiggle", trigger="pleased", length=2.6, weight=3,
      require=["child"], mirror="free")
def _(c):
    c.key(0.3, root_pos=(0, -0.8, 0), head=(-6, 0, 0), ra=(-10, 0, 30), la=(-10, 0, 30))
    c.cycle(0.4, 1.8, 0.5,
            dict(root=(0, 0, 8), head=(-6, 0, -8), ra=(-10, 0, 40), la=(-10, 0, 20), root_pos=(0, -1.2, 0)),
            dict(root=(0, 0, -8), head=(-6, 0, 8), ra=(-10, 0, 20), la=(-10, 0, 40), root_pos=(0, -0.4, 0)))
    c.key(2.2, root=(0, 0, 0), head=(0, 0, 0), ra=(0, 0, 0), la=(0, 0, 0), root_pos=(0, 0, 0))
    c.key(2.6)


# -- annoyed: still upset with you ------------------------------------------------------------------------------

@clip("annoyed_turn_away", "Turns away with the arms folded", trigger="annoyed", length=3.6, weight=3,
      require=["adult"])
def _(c):
    c.key(0.45, root=(0, -30, 0), head=(-8, -10, 0), right_veil=(-4, 0, -10), left_veil=(-4, 0, -10), **FOLDED)
    c.key(0.65, root=(0, -34, 0))
    # a huff: the shoulders lift and drop, chin up
    c.key(1.0, ra_pos=(0, -0.7, 0), la_pos=(0, -0.7, 0), head=(-12, -12, 0))
    c.key(1.3, ra_pos=(0, 0.3, 0), la_pos=(0, 0.3, 0), head=(-8, -10, 0))
    c.key(2.7, root=(0, -32, 0), head=(-8, -8, 0), ra_pos=(0, 0, 0), la_pos=(0, 0, 0), right_veil=(-4, 0, -10),
          left_veil=(-4, 0, -10), **FOLDED)
    c.key(3.6)


@clip("annoyed_huff_flick", "A sharp huff and a flick of the veils", trigger="annoyed", length=2.8, weight=2,
      require=["adult"], mirror="free")
def _(c):
    c.key(0.4, ra_pos=(0, -1.0, 0), la_pos=(0, -1.0, 0), head=(-10, 0, 0), body=(-3, 0, 0), root_pos=(0, -0.6, 0))
    # the breath goes out in one sharp huff: arms stiff at the sides, both veils snapped out and back
    c.key(0.62, ra_pos=(0, 0.5, 0), la_pos=(0, 0.5, 0), head=(10, -6, 0), body=(3, 0, 0), root_pos=(0, 0.6, 0),
          ra=(14, 0, -16), la=(14, 0, -16), rf=(14, 0, 0), lf=(14, 0, 0), right_veil=(16, 0, 34),
          left_veil=(16, 0, 34), right_veil2=(-16, 0, 0), left_veil2=(-16, 0, 0))
    c.key(0.85, right_veil=(4, 0, 8), left_veil=(4, 0, 8), right_veil2=(10, 0, 0), left_veil2=(10, 0, 0),
          right_veil3=(-10, 0, 0), left_veil3=(-10, 0, 0))
    c.key(1.1, right_veil2=(-4, 0, 0), left_veil2=(-4, 0, 0), right_veil3=(6, 0, 0), left_veil3=(6, 0, 0))
    c.key(1.35, head=(4, -14, 0), body=(0, 0, 0), root=(0, -14, 0), right_veil=(0, 0, 0), left_veil=(0, 0, 0),
          right_veil2=(0, 0, 0), left_veil2=(0, 0, 0), right_veil3=(0, 0, 0), left_veil3=(0, 0, 0),
          ra_pos=(0, 0, 0), la_pos=(0, 0, 0), root_pos=(0, 0, 0))
    c.key(2.0, head=(4, -12, 0), root=(0, -12, 0), ra=(10, 0, -12), la=(10, 0, -12))
    c.key(2.4, head=(0, 0, 0), root=(0, 0, 0), ra=(0, 0, 0), la=(0, 0, 0), rf=(0, 0, 0), lf=(0, 0, 0))
    c.key(2.8)


@clip("annoyed_child_turn", "Turns away with crossed arms", trigger="annoyed", length=3.2, weight=3,
      require=["child"])
def _(c):
    c.key(0.4, root=(0, -46, 0), head=(-10, -12, 0), **FOLDED)
    # a kick of both legs behind, and a peek back to see if you noticed
    c.key(0.75, rl=(26, 0, 0), ll=(26, 0, 0), rs=(50, 0, 0), ls=(50, 0, 0))
    c.key(1.05, rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0))
    c.key(1.8, head=(-10, -12, 0))
    c.key(2.05, head=(-4, 20, 4))
    c.key(2.35, head=(-12, -14, 0))
    c.key(2.7, root=(0, -40, 0), **FOLDED)
    c.key(3.2)


# -- hurt: they take damage --------------------------------------------------------------------------------------

@clip("hurt_flinch_dip", "Flinches and dips in the air with the arms up", trigger="hurt", length=1.8, weight=3,
      require=["adult"], blend=(.05, .4), mirror="free")
def _(c):
    c.key(0.1, head=(16, 0, 0), body=(14, 0, 0), rl=(-34, 0, 0), ll=(-30, 0, 0), rs=(44, 0, 0), ls=(40, 0, 0),
          right_veil=(20, 0, 16), left_veil=(20, 0, 16), root_pos=(0, 2.6, 1.0), hair=(-10, 0, 0), **GUARD)
    c.key(0.35, root_pos=(0, 3.2, 0.8), head=(14, 6, 0))
    c.key(0.8, root_pos=(0, 1.6, 0.4), head=(10, 4, 0), body=(8, 0, 0), right_veil=(4, 0, 4), left_veil=(4, 0, 4),
          ra=(-60, -30, -12), rf=(-60, 0, 0), la=(-56, -30, -12), lf=(-60, 0, 0), rl=(-16, 0, 0), ll=(-14, 0, 0),
          rs=(24, 0, 0), ls=(20, 0, 0), hair=(-4, 0, 0))
    c.key(1.3, root_pos=(0, 0.4, 0), head=(4, 0, 0), body=(0, 0, 0), ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0),
          lf=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0), right_veil=(0, 0, 0),
          left_veil=(0, 0, 0), hair=(0, 0, 0))
    c.key(1.8)


@clip("hurt_hand_side", "Clutches the side", trigger="hurt", length=2.0, weight=2, require=["adult"],
      blend=(.05, .4))
def _(c):
    side = dict(ra=(8, -20, -26), rf=(-80, 0, 0))
    c.key(0.1, head=(12, 0, -10), body=(6, 0, -10), rl=(-6, 0, 0), ll=(-6, 0, 0), la=(-10, 0, 40), lf=(10, 0, 0),
          root_pos=(0, 1.6, 0.6), right_veil=(10, 0, 10), left_veil=(10, 0, 18), **side)
    c.key(0.3, root_pos=(0, 2.0, 0.4), head=(14, 4, -12), body=(8, 0, -12))
    c.key(1.0, root_pos=(0, 0.8, 0), head=(8, 0, -6), body=(4, 0, -6), la=(-6, 0, 20), lf=(0, 0, 0),
          right_veil=(4, 0, 4), left_veil=(4, 0, 6), **side)
    c.key(1.5, root_pos=(0, 0.2, 0), head=(2, 0, 0), body=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0), la=(0, 0, 0),
          ra=(0, 0, 0), rf=(0, 0, 0), right_veil=(0, 0, 0), left_veil=(0, 0, 0))
    c.key(2.0)


@clip("hurt_child_tumble", "Flinches and tumbles over backward", trigger="hurt", length=2.2, weight=3,
      require=["child"], blend=(.05, .4), mirror="free")
def _(c):
    c.key(0.08, head=(14, 0, 0), rl=(-40, 0, 0), ll=(-40, 0, 0), rs=(60, 0, 0), ls=(60, 0, 0), **GUARD)
    # knocked head over heels: fast at first, slowing as it comes round (about the child's middle)
    turn_over(c, 0.1, 1.0, -360, h=4.5, rise=-1.5, steps=12, shape=lambda s: math.sin(math.pi / 2 * s))
    c.key(0.95, head=(14, 0, 0), rl=(-40, 0, 0), ll=(-40, 0, 0), rs=(60, 0, 0), ls=(60, 0, 0), **GUARD)
    # and a little dazed
    c.key(1.25, ra=(-20, 0, 30), rf=(-20, 0, 0), la=(-20, 0, 30), lf=(-20, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0),
          rs=(0, 0, 0), ls=(0, 0, 0))
    c.wobble(1.1, 1.9, 2.5, "head", 10, base=(4, 0, 0), axis=2, decay=0.6)
    c.key(1.8, ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0))
    c.key(2.2)
