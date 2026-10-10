"""Meeting, chatting and parting. The Cirri greet with the whole arm and the veil on that side lifting with it,
bow in the air with a hand on the heart, tell each other about the sky with sweeping hands, and loop for joy.

Bows tip the `body` part at the hips (it carries the legs, so they are turned back to keep hanging) rather than the
waist; veils and the hair tail are counter-turned so they keep hanging when the body or head bends."""
import math

from kit import clip


def bowed(p, legs=1.0, head=0.0, veils=1.0):
    """The body tipped forward p degrees at the hips, with the legs, veils and hair kept hanging."""
    return dict(body=(p, 0, 0), rl=(-p * legs, 0, 0), ll=(-p * legs, 0, 0),
                right_veil=(-p * veils, 0, 0), left_veil=(-p * veils, 0, 0), hair=(-(p + head) * 0.8, 0, 0))


def turn_over(c, t0, t1, deg, h=5.0, rise=0.0, loop=0.0, steps=12):
    """The whole Cirri turned head over heels, deg (+-360) between t0 and t1, about a point h pixels above the
    hips, rising by rise halfway and (loop > 0) travelling a circle of that radius with the head leading; then the
    turn snaps back to 0 unseen (360 is the same pose). It turns the body part (which carries everything, about
    the hips) rather than root: reactions scale root by how fast the Cirri is moving, which would show the snap."""
    for i in range(steps + 1):
        s = i / steps
        e = (1 - math.cos(math.pi * s)) / 2
        r = math.radians(deg * e)
        phi = 2 * math.pi * e
        y = -h + h * math.cos(r) - rise * math.sin(math.pi * e) - loop * math.sin(phi)
        z = h * math.sin(r) + loop * (1 - math.cos(phi)) * (1 if deg < 0 else -1)
        c.key(t0 + (t1 - t0) * s, body=(deg * e, 0, 0), root_pos=(0, y, z))
    c.key(t1 + 0.0001, body=(0, 0, 0), root_pos=(0, 0, 0))


def sampled(c, t0, t1, fn, step=0.1):
    """Keys fn(t) (a dict of channels) every step from t0 to t1."""
    n = max(2, round((t1 - t0) / step))
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        c.key(t, **fn(t))


def env(t, t0, t1, ramp):
    """1 inside t0..t1, easing in and out over ramp seconds."""
    return max(0.0, min(1.0, (t - t0) / ramp, (t1 - t) / ramp))


def sn(t, period, phase=0.0):
    return math.sin((t / period + phase) * math.tau)


HEART = dict(ra=(-22, -38, -18), rf=(-78, 0, 0))
CLASP = dict(ra=(-22, -30, -18), rf=(-62, 0, 0), la=(-24, -30, -16), lf=(-64, 0, 0))


# -- greet ------------------------------------------------------------------------------------------------------

@clip("greet_veil_wave", "Waves with the whole arm and veil", trigger="greet", length=3.0, weight=3,
      require=["adult"])
def _(c):
    up = dict(ra=(-10, 0, 120), rf=(14, 0, 0), right_veil=(28, 0, 30), right_veil2=(-10, 0, 0),
              right_veil3=(-12, 0, 0), right_veil4=(-10, 0, 0))
    c.key(0.45, head=(-4, 0, -7), body=(0, 0, 4), root_pos=(0, -1.0, 0), **up)
    for i, t in enumerate((0.7, 1.05, 1.4, 1.75)):
        side = 1 if i % 2 == 0 else -1
        c.key(t, ra=(-10, 0, 120 + 20 * side), right_veil=(28 + 6 * side, 0, 30 + 12 * side),
              right_veil2=(-10 - 12 * side, 0, 0), right_veil3=(-12 + 14 * side, 0, 0),
              right_veil4=(-10 - 12 * side, 0, 0), head=(-4, 0, -7 + 3 * side))
    c.key(2.05, **up)
    c.key(2.5, ra=(-4, 0, 14), rf=(0, 0, 0), right_veil=(6, 0, 6), right_veil2=(0, 0, 0), right_veil3=(0, 0, 0),
          right_veil4=(0, 0, 0), head=(0, 0, 0), body=(0, 0, 0), root_pos=(0, 0, 0))
    c.key(3.0)


@clip("greet_air_bow", "A bow in the air with a hand on the heart", trigger="greet", length=3.2, weight=3,
      require=["adult"])
def _(c):
    c.key(0.45, la=(12, 0, 16), lf=(14, 0, 0), head=(4, 0, 0), **HEART)
    c.key(1.0, la=(16, 0, 22), root_pos=(0, 0.6, 0), head=(14, 0, 0), **HEART, **bowed(26, head=14))
    c.key(1.65, la=(16, 0, 22), root_pos=(0, 0.6, 0), head=(15, 0, 0), **HEART, **bowed(28, head=15))
    c.key(2.25, la=(4, 0, 6), lf=(0, 0, 0), root_pos=(0, -0.3, 0), head=(-2, 0, 5), **HEART, **bowed(0))
    c.key(2.6, ra=(-6, -6, 0), rf=(-10, 0, 0), la=(0, 0, 0), head=(0, 0, 2), root_pos=(0, 0, 0))
    c.key(3.2)


@clip("greet_loop", "A delighted little loop", trigger="greet", length=3.2, weight=1, require=["adult"],
      boost={"manner:flighty": 5}, mirror="free")
def _(c):
    c.key(0.3, ra=(6, 0, 10), la=(6, 0, 10), rl=(-20, 0, 0), ll=(-20, 0, 0), rs=(30, 0, 0), ls=(30, 0, 0),
          head=(6, 0, 0))
    tuck = dict(ra=(-10, 0, 60), la=(-10, 0, 60), rf=(10, 0, 0), lf=(10, 0, 0), rl=(-50, 0, 0), ll=(-50, 0, 0),
                rs=(70, 0, 0), ls=(70, 0, 0), right_veil=(40, 0, 20), left_veil=(40, 0, 20), head=(-10, 0, 0))
    c.key(0.5, **tuck)
    turn_over(c, 0.5, 1.5, -360, h=5, rise=2, loop=2.5)
    c.key(1.4, **tuck)
    # open out, ta-da, and a quick wave
    c.key(1.75, ra=(-10, 0, 130), la=(-10, 0, 70), rf=(10, 0, 0), lf=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0),
          rs=(0, 0, 0), ls=(0, 0, 0), right_veil=(10, 0, 30), left_veil=(10, 0, 20), head=(-6, 0, -6))
    c.key(2.0, ra=(-10, 0, 150), head=(-6, 0, 4))
    c.key(2.25, ra=(-10, 0, 125), head=(-6, 0, -4))
    c.key(2.5, ra=(-10, 0, 145))
    c.key(2.85, ra=(0, 0, 10), la=(0, 0, 8), rf=(0, 0, 0), right_veil=(0, 0, 0), left_veil=(0, 0, 0), head=(0, 0, 0))
    c.key(3.2)


@clip("greet_shy", "A shy half-wave", trigger="greet", length=3.0, weight=1, require=["adult"],
      boost={"manner:shy": 5})
def _(c):
    c.key(0.5, ra=(-30, -14, -14), rf=(-86, 0, 0), la=(-20, -30, -14), lf=(-60, 0, 0), head=(14, -10, 6),
          root=(0, -10, 0), root_pos=(0, 0, 0.8), right_veil=(-4, 0, -12), left_veil=(-4, 0, -12))
    c.wobble(0.6, 1.7, 3, "rf", 12, base=(-86, 0, 0))
    c.key(1.15, head=(2, -4, 2))
    c.key(1.7, head=(16, -12, 8))
    c.key(2.4, ra=(-4, 0, 0), rf=(-10, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), head=(4, 0, 0), root=(0, 0, 0),
          root_pos=(0, 0, 0), right_veil=(0, 0, 0), left_veil=(0, 0, 0))
    c.key(3.0)


@clip("greet_open_arms", "Opens the arms to the wind and you", trigger="greet", length=3.0, weight=2,
      require=["adult"], mirror="free")
def _(c):
    c.key(0.3, ra=(4, 0, -6), la=(4, 0, -6), head=(4, 0, 0))
    wide = dict(ra=(-36, 34, 40), la=(-36, 34, 40), rf=(16, 0, 0), lf=(16, 0, 0), head=(-8, 0, 0),
                right_veil=(24, 0, 30), left_veil=(24, 0, 30), right_veil2=(-8, 0, 0), left_veil2=(-8, 0, 0),
                root_pos=(0, -1.6, 0), body=(-4, 0, 0))
    c.key(0.8, **wide)
    c.key(1.9, **{**wide, "head": (-6, 0, 5), "root_pos": (0, -2.0, 0)})
    c.key(2.4, ra=(-6, 0, 6), la=(-6, 0, 6), rf=(0, 0, 0), lf=(0, 0, 0), head=(2, 0, 2), right_veil=(4, 0, 6),
          left_veil=(4, 0, 6), right_veil2=(0, 0, 0), left_veil2=(0, 0, 0), root_pos=(0, 0, 0), body=(0, 0, 0))
    c.key(3.0)


@clip("greet_child_wave", "Waves with both arms", trigger="greet", length=2.6, weight=3, require=["child"],
      mirror="free")
def _(c):
    c.key(0.3, ra=(-10, 0, 120), la=(-10, 0, 120), rf=(10, 0, 0), lf=(10, 0, 0), head=(-6, 0, 0),
          root_pos=(0, -0.5, 0))
    c.cycle(0.3, 1.9, 0.5,
            dict(ra=(-10, 0, 150), la=(-10, 0, 105), head=(-8, 0, -8), root_pos=(0, -1.6, 0), body=(0, 0, -4)),
            dict(ra=(-10, 0, 105), la=(-10, 0, 150), head=(-8, 0, 8), root_pos=(0, 0.2, 0), body=(0, 0, 4)))
    c.key(2.25, ra=(0, 0, 8), la=(0, 0, 8), rf=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0), root_pos=(0, 0, 0),
          body=(0, 0, 0))
    c.key(2.6)


@clip("greet_child_somersault", "A somersault hello", trigger="greet", length=3.0, weight=2, require=["child"],
      mirror="free")
def _(c):
    tuck = dict(ra=(-50, -10, 10), la=(-50, -10, 10), rf=(-60, 0, 0), lf=(-60, 0, 0), rl=(-80, 0, 0),
                ll=(-80, 0, 0), rs=(100, 0, 0), ls=(100, 0, 0), head=(14, 0, 0))
    c.key(0.25, root_pos=(0, -0.6, 0), head=(-6, 0, 0))
    c.key(0.45, **tuck)
    turn_over(c, 0.45, 1.45, 360, h=0, rise=2)
    c.key(1.4, **tuck)
    c.key(1.75, ra=(-10, 0, 150), la=(-10, 0, 150), rf=(10, 0, 0), lf=(10, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0),
          rs=(0, 0, 0), ls=(0, 0, 0), head=(-10, 0, 0))
    c.key(2.05, ra=(-10, 0, 130), la=(-10, 0, 160), head=(-8, 0, 8))
    c.key(2.35, ra=(-10, 0, 160), la=(-10, 0, 130), head=(-8, 0, -8))
    c.key(2.7, ra=(0, 0, 6), la=(0, 0, 6), rf=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0))
    c.key(3.0)


# -- farewell ---------------------------------------------------------------------------------------------------

@clip("farewell_drift_wave", "Waves while drifting back", trigger="farewell", length=3.4, weight=3,
      require=["adult"])
def _(c):
    up = dict(ra=(-10, 0, 112), rf=(12, 0, 0), right_veil=(22, 0, 22), right_veil2=(-8, 0, 0))
    c.key(0.45, head=(-2, 0, -6), root_pos=(0, -0.4, 0.6), rl=(-6, 0, 0), ll=(-8, 0, 0), **up)
    for i, t in enumerate((0.75, 1.15, 1.55, 1.95)):
        side = 1 if i % 2 == 0 else -1
        c.key(t, ra=(-10, 0, 112 + 16 * side), right_veil2=(-8 - 10 * side, 0, 0),
              right_veil3=(10 * side, 0, 0), head=(-2, 0, -6 + 3 * side))
    c.key(2.3, root_pos=(0, -1.4, 3.0), rl=(-12, 0, 0), ll=(-14, 0, 0), right_veil3=(0, 0, 0), **up)
    c.key(2.8, ra=(-4, 0, 10), rf=(0, 0, 0), right_veil=(4, 0, 4), right_veil2=(0, 0, 0), head=(0, 0, 0),
          root_pos=(0, -0.8, 1.4), rl=(-4, 0, 0), ll=(-4, 0, 0))
    c.key(3.4)


@clip("farewell_bow", "A parting bow with an open hand", trigger="farewell", length=3.2, weight=2,
      require=["adult"])
def _(c):
    c.key(0.4, head=(4, 0, 0), **HEART)
    c.key(0.95, head=(14, 0, 0), la=(14, 0, 18), **HEART, **bowed(22, head=14))
    # still bowed, the hand on the heart opens out to you: something of the heart, for the road
    c.key(1.55, head=(12, 0, 0), ra=(-58, 18, -8), rf=(-22, 0, 0), la=(14, 0, 18), **bowed(22, head=12))
    c.key(2.15, head=(-2, 0, 6), ra=(-34, 22, 0), rf=(-14, 0, 0), la=(4, 0, 6), root=(0, 8, 0), **bowed(0))
    c.key(2.7, ra=(-4, 0, 4), rf=(-4, 0, 0), la=(0, 0, 0), head=(0, 0, 2), root=(0, 4, 0))
    c.key(3.2)


@clip("farewell_wind_kiss", "Blows a breath of wind off the palm", trigger="farewell", length=3.6, weight=2,
      require=["adult"])
def _(c):
    palm = dict(ra=(-58, -24, -16), rf=(-72, 0, 0))
    c.key(0.5, head=(8, 0, 0), **palm)
    # a breath in: the shoulders rise and the body leans back a touch
    c.key(0.95, head=(-4, 0, 0), ra_pos=(0, -0.6, 0), la_pos=(0, -0.6, 0), body=(-4, 0, 0), rl=(4, 0, 0),
          ll=(4, 0, 0), **palm)
    # and blown off the palm: the hand sweeps out to you and both veils billow after it
    c.key(1.3, head=(10, 0, 0), ra=(-80, 22, -6), rf=(-10, 0, 0), ra_pos=(0, 0, 0), la_pos=(0, 0, 0),
          body=(6, 0, 0), rl=(-6, 0, 0), ll=(-6, 0, 0), right_veil=(30, 0, 30), left_veil=(30, 0, 30),
          right_veil2=(-14, 0, 0), left_veil2=(-14, 0, 0))
    c.wave(1.4, 2.6, 0.6, "right_veil3", 14)
    c.wave(1.4, 2.6, 0.6, "left_veil3", 14, phase=0.2)
    c.key(1.9, head=(2, 0, 6), ra=(-78, 24, -6), body=(2, 0, 0), rl=(-2, 0, 0), ll=(-2, 0, 0),
          right_veil=(24, 0, 24), left_veil=(24, 0, 24), right_veil2=(-8, 0, 0), left_veil2=(-8, 0, 0))
    c.key(2.9, ra=(-6, 0, 4), rf=(-4, 0, 0), head=(0, 0, 2), body=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0),
          right_veil=(0, 0, 0), left_veil=(0, 0, 0), right_veil2=(0, 0, 0), left_veil2=(0, 0, 0))
    c.key(3.6)


@clip("farewell_child_bob_away", "Waves and bobs away backward", trigger="farewell", length=2.8, weight=3,
      require=["child"], mirror="free")
def _(c):
    c.key(0.3, ra=(-10, 0, 140), rf=(10, 0, 0), la=(-10, 0, 40), head=(-6, 0, -6))
    for i, t in enumerate((0.55, 0.95, 1.35, 1.75)):
        side = 1 if i % 2 == 0 else -1
        c.key(t, ra=(-10, 0, 140 + 18 * side), head=(-6, 0, -6 * side), body=(0, 0, 5 * side),
              root_pos=(0, -1.2 if side > 0 else 0, 0.8 * (i + 1)), rl=(-20 if side > 0 else 4, 0, 0),
              ll=(4 if side > 0 else -20, 0, 0))
    c.key(2.2, ra=(0, 0, 10), rf=(0, 0, 0), la=(0, 0, 6), head=(0, 0, 0), body=(0, 0, 0), root_pos=(0, -0.4, 1.6),
          rl=(0, 0, 0), ll=(0, 0, 0))
    c.key(2.8)


@clip("farewell_child_blow_spin", "Blows a breath of wind and twirls", trigger="farewell", length=3.2,
      weight=2, require=["child"], mirror="free")
def _(c):
    cup = dict(ra=(-56, -26, -16), rf=(-74, 0, 0), la=(-56, -26, -16), lf=(-74, 0, 0))
    c.key(0.4, head=(8, 0, 0), **cup)
    c.key(0.75, head=(-6, 0, 0), ra_pos=(0, -0.5, 0), la_pos=(0, -0.5, 0), **cup)
    c.key(1.05, head=(8, 0, 0), ra=(-80, 30, 0), rf=(-6, 0, 0), la=(-80, 30, 0), lf=(-6, 0, 0),
          ra_pos=(0, 0, 0), la_pos=(0, 0, 0), right_veil=(30, 0, 24), left_veil=(30, 0, 24))
    # then a twirl with the arms out
    c.key(1.3, body=(0, 0, 0), ra=(-10, 0, 70), la=(-10, 0, 70), rf=(0, 0, 0), lf=(0, 0, 0), head=(-4, 0, 0),
          right_veil=(20, 0, 40), left_veil=(20, 0, 40))
    c.key(1.7, body=(0, 140, 0), root_pos=(0, -1.2, 0))
    c.key(2.1, body=(0, 290, 0), root_pos=(0, -1.0, 0))
    c.key(2.4, body=(0, 360, 0), root_pos=(0, -0.3, 0), ra=(-10, 0, 60), la=(-10, 0, 60))
    c.key(2.4001, body=(0, 0, 0))
    c.key(2.8, ra=(0, 0, 6), la=(0, 0, 6), head=(0, 0, 0), root_pos=(0, 0, 0), right_veil=(0, 0, 0),
          left_veil=(0, 0, 0))
    c.key(3.2)


# -- chatting with a neighbour: telling ------------------------------------------------------------------------

@clip("chat_sweep_tell", "Tells it with sweeping hands", trigger="chat_speak", length=3.8, weight=3,
      require=["adult"])
def _(c):
    c.key(0.4, ra=(-50, -30, -14), rf=(-50, 0, 0), la=(-14, -6, 0), lf=(-20, 0, 0), head=(2, -10, 0))
    c.key(1.2, ra=(-62, 50, 0), rf=(-22, 0, 0), head=(-2, 14, 0), body=(0, 6, 0))
    c.key(1.5, ra=(-60, 54, 2), head=(0, 16, 0))
    c.key(1.8, ra=(-30, 10, 0), rf=(-30, 0, 0), la=(-50, -30, -14), lf=(-50, 0, 0), head=(2, 0, 0), body=(0, 0, 0))
    c.key(2.55, la=(-62, 50, 0), lf=(-22, 0, 0), head=(-2, -14, 0), body=(0, -6, 0))
    c.key(2.8, la=(-60, 54, 2), head=(0, -14, 0))
    c.key(3.25, ra=(-30, 20, 6), rf=(-30, 0, 0), la=(-30, 20, 6), lf=(-30, 0, 0), head=(4, 0, 4), body=(0, 0, 0))
    c.key(3.8)


@clip("chat_point_sky", "Points up at the sky", trigger="chat_speak", length=3.8, weight=2, require=["adult"])
def _(c):
    c.key(0.45, ra=(-150, 10, -10), rf=(16, 0, 0), head=(-24, 6, 0), body=(-4, 0, 0), rl=(4, 0, 0), ll=(4, 0, 0),
          la=(-6, 0, 6), hair=(18, 0, 0))
    # traces the wind's road across the sky
    c.key(1.3, ra=(-142, 30, -6), head=(-24, 16, 0), hair=(18, 0, 0))
    c.key(2.0, ra=(-140, 44, -4), head=(-20, 24, 0), hair=(16, 0, 0))
    c.key(2.5, ra=(-48, 20, 0), rf=(-36, 0, 0), head=(4, 0, 4), body=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0),
          hair=(0, 0, 0))
    c.key(2.85, head=(10, 0, 4))
    c.key(3.3, ra=(-6, 0, 2), rf=(-6, 0, 0), la=(0, 0, 0), head=(0, 0, 0))
    c.key(3.8)


@clip("chat_whale_size", "Shows how big the whale was", trigger="chat_speak", length=4.6, weight=2,
      require=["adult"], mirror="free")
def _(c):
    c.key(0.5, ra=(-60, 50, 6), la=(-60, 50, 6), rf=(8, 0, 0), lf=(8, 0, 0), head=(-4, 0, 0))
    c.key(1.0, ra=(-50, 78, 22), la=(-50, 78, 22), root_pos=(0, -1.4, 0), head=(-10, 0, 0),
          right_veil=(14, 0, 26), left_veil=(14, 0, 26))
    c.key(1.5, ra=(-52, 80, 24), la=(-52, 80, 24), root_pos=(0, -1.6, 0), head=(-10, 0, 2))
    # and it swam like this: one hand rolls slowly through the air, the eyes following it

    def swim(t):
        e = min(1.0, (t - 1.8) / 0.35)          # from the wide pose into the swim
        w = env(t, 1.8, 3.6, 0.35)              # the swimming itself
        return dict(ra=(-70 * e - 52 * (1 - e) + 12 * sn(t - 1.8, 0.9) * w, 30 * e + 80 * (1 - e), 22 * (1 - e)),
                    rf=(-20 * e + 8 * (1 - e) + 22 * sn(t - 1.8, 0.9, -0.15) * w, 0, 0),
                    head=(-4 * e - 10 * (1 - e) + 4 * sn(t - 1.8, 0.9) * w, -10 * e + 22 * (t - 1.8) / 1.8 * e,
                          2 * (1 - e)))
    sampled(c, 1.8, 3.6, swim, step=0.15)
    c.key(1.8, la=(-20, 20, 8), lf=(-20, 0, 0), root_pos=(0, -0.6, 0), right_veil=(4, 0, 8), left_veil=(4, 0, 8))
    c.key(4.0, ra=(-6, 0, 4), rf=(-4, 0, 0), la=(-4, 0, 4), lf=(-4, 0, 0), head=(0, 0, 0), root_pos=(0, 0, 0),
          right_veil=(0, 0, 0), left_veil=(0, 0, 0))
    c.key(4.6)


@clip("chat_laugh_back", "Laughs with the head thrown back", trigger="chat_speak", length=3.2, weight=2,
      mirror="free")
def _(c):
    c.key(0.3, head=(-22, 0, 0), body=(-10, 0, 0), rl=(10, 0, 0), ll=(10, 0, 0), ra=(-20, -36, -18),
          rf=(-60, 0, 0), la=(-6, 0, 14), hair=(24, 0, 0))
    c.wobble(0.35, 2.0, 7, "ra_pos", 0.6, axis=1)
    c.wobble(0.35, 2.0, 7, "la_pos", 0.6, axis=1)
    c.wobble(0.35, 2.0, 3.5, "root_pos", 0.7, axis=1)
    c.wobble(0.35, 2.0, 3.5, "head", 5, base=(-22, 0, 0), axis=2, decay=0.4)
    c.wobble(0.35, 2.0, 3.5, "right_veil2", 8, decay=0.3)
    c.wobble(0.4, 2.0, 3.5, "left_veil2", 8, decay=0.3)
    c.key(2.0, body=(-8, 0, 0), rl=(8, 0, 0), ll=(8, 0, 0), hair=(20, 0, 0))
    c.key(2.35, head=(10, 0, 4), body=(6, 0, 0), rl=(-6, 0, 0), ll=(-6, 0, 0), hair=(-10, 0, 0))
    c.key(2.8, head=(0, 0, 0), body=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0), ra=(0, 0, 0), rf=(0, 0, 0),
          la=(0, 0, 0), hair=(0, 0, 0))
    c.key(3.2)


@clip("chat_count_points", "Counts the points off on the fingers", trigger="chat_speak", length=4.2, weight=2,
      require=["adult"])
def _(c):
    c.key(0.4, la=(-44, -16, -16), lf=(-56, 0, 0), ra=(-40, -30, -16), rf=(-78, 0, 0), head=(6, 0, 0))
    for i, t in enumerate((0.8, 1.5, 2.2)):
        c.key(t, ra=(-44 - i * 2, -34 + i * 5, -16), rf=(-88, 0, 0), head=(12, -6 + i * 6, 0))
        c.key(t + 0.32, ra=(-38 - i * 2, -28 + i * 5, -16), rf=(-74, 0, 0), head=(4, -4 + i * 6, 0))
    c.key(3.1, ra=(-36, 20, 4), rf=(-34, 0, 0), la=(-36, 20, 4), lf=(-34, 0, 0), head=(4, 0, 6))
    c.key(3.6, ra=(-6, 0, 2), rf=(-6, 0, 0), la=(-6, 0, 2), lf=(-6, 0, 0), head=(0, 0, 0))
    c.key(4.2)


@clip("chat_sing_phrase", "Sings a phrase and shapes it with a hand", trigger="chat_speak", length=4.2,
      weight=1, boost={"routine:evensong": 6})
def _(c):
    c.key(0.5, ra=(-50, 14, 0), rf=(-50, 0, 0), head=(-6, 0, 6))

    def tune(t):
        e = env(t, 0.5, 3.4, 0.4)
        note = sn(t - 0.5, 1.45)
        return dict(ra=(-50 - 18 * note * e, 14 + 12 * sn(t - 0.5, 2.9) * e, 0), rf=(-50 + 10 * note * e, 0, 0),
                    head=(-6 - 6 * note * e, 0, 6 * e + 4 * sn(t - 0.5, 2.9, 0.25) * e),
                    body=(0, 0, 4 * sn(t - 0.5, 2.9) * e),
                    right_veil=(6 * e, 0, 8 * e + 6 * sn(t - 0.5, 2.9, -0.1) * e),
                    left_veil=(6 * e, 0, 8 * e - 6 * sn(t - 0.5, 2.9, -0.1) * e))
    sampled(c, 0.5, 3.4, tune, step=0.12)
    c.key(3.8, ra=(-6, 0, 2), rf=(-6, 0, 0), head=(4, 0, 0), body=(0, 0, 0), right_veil=(0, 0, 0),
          left_veil=(0, 0, 0))
    c.key(4.2)


@clip("chat_child_bounce", "Bounces as they tell it", trigger="chat_speak", length=2.8, weight=3,
      require=["child"], mirror="free")
def _(c):
    c.key(0.25, ra=(-20, 0, 40), la=(-20, 0, 40), head=(-6, 0, 0))
    c.cycle(0.25, 2.05, 0.45,
            dict(ra=(-30, 0, 70), la=(-30, 0, 30), rf=(-20, 0, 0), root_pos=(0, -1.6, 0), head=(-8, 0, -6),
                 rl=(-24, 0, 0), ll=(-10, 0, 0), rs=(30, 0, 0), ls=(30, 0, 0)),
            dict(ra=(-30, 0, 30), la=(-30, 0, 70), rf=(0, 0, 0), root_pos=(0, 0.3, 0), head=(-2, 0, 6),
                 rl=(-6, 0, 0), ll=(-20, 0, 0), rs=(10, 0, 0), ls=(10, 0, 0)))
    c.key(2.4, ra=(0, 0, 6), la=(0, 0, 6), rf=(0, 0, 0), root_pos=(0, 0, 0), head=(0, 0, 0), rl=(0, 0, 0),
          ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0))
    c.key(2.8)


@clip("chat_child_this_big", "This big! And it went whoosh!", trigger="chat_speak", length=3.2, weight=2,
      require=["child"], mirror="free")
def _(c):
    c.key(0.35, ra=(-60, 60, 20), la=(-60, 60, 20), rf=(6, 0, 0), lf=(6, 0, 0), head=(-8, 0, 0),
          root_pos=(0, -1.2, 0))
    c.key(0.75, ra=(-50, 84, 30), la=(-50, 84, 30), root_pos=(0, -2.0, 0), head=(-12, 0, 0),
          rl=(-20, 0, 0), ll=(-20, 0, 0), rs=(30, 0, 0), ls=(30, 0, 0))
    c.key(1.1, root_pos=(0, -1.6, 0))
    # whoosh: a sweep of the arm and a tip forward after it
    c.key(1.45, ra=(-120, -20, 0), la=(-20, 0, 30), rf=(0, 0, 0), head=(-14, -10, 0), root=(-10, 0, 0),
          root_pos=(0, -0.6, 0))
    c.key(1.9, ra=(-40, 60, 20), head=(6, 20, 0), root=(22, 0, 0), root_pos=(0, -0.4, -1.2), rl=(10, 0, 0),
          ll=(14, 0, 0), rs=(20, 0, 0), ls=(20, 0, 0))
    c.key(2.3, root=(0, 0, 0), root_pos=(0, 0, 0), head=(-4, 0, 6), ra=(-20, 0, 30), la=(-20, 0, 30),
          rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0))
    c.key(2.8, ra=(0, 0, 4), la=(0, 0, 4), head=(0, 0, 0), rf=(0, 0, 0), lf=(0, 0, 0))
    c.key(3.2)


# -- chatting with a neighbour: listening ----------------------------------------------------------------------

@clip("chat_nod_along", "Nods along", trigger="chat_listen", length=3.4, weight=3)
def _(c):
    c.key(0.5, head=(2, 0, 5), **CLASP)
    for t in (0.9, 1.8):
        c.key(t, head=(13, 0, 4), hair=(-10, 0, 0))
        c.key(t + 0.4, head=(1, 0, 5), hair=(0, 0, 0))
    c.key(2.8, head=(2, 0, 2), **CLASP)
    c.key(3.4)


@clip("chat_head_tilt", "Tilts the head in wonder", trigger="chat_listen", length=3.6, weight=3, mirror="free")
def _(c):
    c.key(0.7, head=(-2, 8, 15), body=(0, 0, -3), la=(-14, -10, -8), lf=(-30, 0, 0), right_veil=(0, 0, 6))
    c.key(2.2, head=(-4, 10, 17), body=(0, 0, -4))
    c.key(2.6, head=(8, 4, 10), body=(0, 0, -2))
    c.key(3.0, head=(2, 2, 4), body=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), right_veil=(0, 0, 0))
    c.key(3.6)


@clip("chat_hand_chin", "A hand to the chin", trigger="chat_listen", length=4.0, weight=2, require=["adult"])
def _(c):
    chin = dict(ra=(-42, -30, -18), rf=(-112, 0, 0), la=(-26, -40, -18), lf=(-88, 0, 0))
    c.key(0.6, head=(6, 0, -5), **chin)
    for t in (1.2, 2.3):
        c.key(t, head=(11, 0, -5))
        c.key(t + 0.45, head=(4, 0, -4))
    c.key(3.3, head=(4, 0, -2), **chin)
    c.key(4.0)


@clip("chat_laugh_joke", "Laughs at the joke", trigger="chat_listen", length=3.0, weight=2, mirror="free")
def _(c):
    c.key(0.3, ra=(-44, -32, -18), rf=(-108, 0, 0), head=(8, 0, 8), body=(4, 0, 0), rl=(-4, 0, 0), ll=(-4, 0, 0))
    c.wobble(0.35, 1.8, 6, "ra_pos", 0.5, axis=1)
    c.wobble(0.35, 1.8, 6, "la_pos", 0.5, axis=1)
    c.wobble(0.35, 1.8, 3, "root_pos", 0.6, axis=1)
    c.wobble(0.35, 1.8, 3, "head", 4, base=(8, 0, 8), axis=0, decay=0.4)
    # a little flick of the veils at the end of it
    c.key(1.8, la=(-30, 20, 10), lf=(-30, 0, 0), right_veil=(0, 0, 0), left_veil=(0, 0, 0))
    c.key(2.05, right_veil=(10, 0, 18), left_veil=(10, 0, 18))
    c.key(2.5, ra=(-4, 0, 2), rf=(-6, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0), body=(0, 0, 0),
          rl=(0, 0, 0), ll=(0, 0, 0), right_veil=(0, 0, 0), left_veil=(0, 0, 0))
    c.key(3.0)


@clip("chat_drift_closer", "Drifts a little closer to hear", trigger="chat_listen", length=4.4, weight=2,
      require=["adult"])
def _(c):
    c.key(1.2, root_pos=(0, -0.4, -2.6), head=(-2, 0, 8), **CLASP, **bowed(7, legs=0.6))
    c.key(2.6, root_pos=(0, -0.2, -3.0), head=(4, 0, 10), **CLASP, **bowed(8, legs=0.6))
    c.key(3.0, head=(10, 0, 6))
    c.key(3.8, root_pos=(0, 0, -0.8), head=(2, 0, 2), ra=(-6, 0, 0), rf=(-10, 0, 0), la=(-6, 0, 0), lf=(-10, 0, 0),
          **bowed(0))
    c.key(4.4)


@clip("chat_hum_along", "Hums along with a hand on the heart", trigger="chat_listen", length=4.2, weight=1,
      boost={"routine:evensong": 6}, mirror="free")
def _(c):
    c.key(0.6, head=(-4, 0, 6), **HEART)

    def sway(t):
        e = env(t, 0.6, 3.5, 0.5)
        return dict(head=(-4 - 4 * sn(t - 0.6, 1.45) * e, 0, 6 + 8 * sn(t - 0.6, 2.9) * e),
                    body=(0, 0, -5 * sn(t - 0.6, 2.9) * e),
                    right_veil=(4 * e, 0, 6 * e + 6 * sn(t - 0.6, 2.9, -0.12) * e),
                    left_veil=(4 * e, 0, 6 * e - 6 * sn(t - 0.6, 2.9, -0.12) * e))
    sampled(c, 0.6, 3.5, sway, step=0.12)
    c.key(3.8, head=(6, 0, 0), ra=(-10, -10, 0), rf=(-20, 0, 0))
    c.key(4.2)


@clip("chat_child_kick_listen", "Kicks the legs and listens", trigger="chat_listen", length=3.2, weight=3,
      require=["child"], mirror="free")
def _(c):
    c.key(0.4, head=(0, 6, 10), **CLASP)
    c.cycle(0.4, 2.6, 0.55, dict(rl=(-34, 0, 0), rs=(20, 0, 0), ll=(6, 0, 0), ls=(50, 0, 0)),
            dict(rl=(6, 0, 0), rs=(50, 0, 0), ll=(-34, 0, 0), ls=(20, 0, 0)))
    c.key(1.6, head=(4, 8, 14))
    c.key(2.6, head=(2, 4, 6), **CLASP)
    c.key(3.0, rl=(0, 0, 0), rs=(0, 0, 0), ll=(0, 0, 0), ls=(0, 0, 0), head=(0, 0, 0))
    c.key(3.2)


@clip("chat_child_wow", "Hands to the cheeks: wow", trigger="chat_listen", length=3.0, weight=2,
      require=["child"], mirror="free")
def _(c):
    cheeks = dict(ra=(-58, -12, -14), rf=(-122, 0, 0), la=(-58, -12, -14), lf=(-122, 0, 0))
    c.key(0.4, head=(-8, 0, 0), body=(-6, 0, 0), rl=(6, 0, 0), ll=(6, 0, 0), root_pos=(0, -0.6, 0), **cheeks)
    c.key(0.7, root_pos=(0, -1.6, 0), rl=(-30, 0, 0), ll=(-30, 0, 0), rs=(50, 0, 0), ls=(50, 0, 0))
    c.key(1.0, root_pos=(0, -0.2, 0), rl=(6, 0, 0), ll=(6, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0))
    c.wobble(1.1, 2.1, 3, "head", 8, base=(-8, 0, 0), axis=2)
    c.key(2.5, head=(0, 0, 0), body=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0), root_pos=(0, 0, 0), ra=(0, 0, 0),
          rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0))
    c.key(3.0)
