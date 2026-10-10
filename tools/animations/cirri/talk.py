"""Conversation: small, specific gestures while a Cirri's line types out to you, and how they listen while you
choose a reply. Grown-ups offer an open palm, shape clouds, lean in to confide and gaze off at far skies; children
flap, whisper secrets and rock on the air like little boats."""
import math

from kit import clip


def bowed(p, legs=1.0, head=0.0, veils=1.0):
    """The body tipped forward p degrees at the hips, with the legs, veils and hair kept hanging."""
    return dict(body=(p, 0, 0), rl=(-p * legs, 0, 0), ll=(-p * legs, 0, 0),
                right_veil=(-p * veils, 0, 0), left_veil=(-p * veils, 0, 0), hair=(-(p + head) * 0.8, 0, 0))


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
LOW_CLASP = dict(ra=(-14, -24, -18), rf=(-48, 0, 0), la=(-16, -24, -16), lf=(-50, 0, 0))


# -- talk: gestures while their line types out ------------------------------------------------------------------

@clip("talk_open_palm", "An open palm", trigger="talk", length=3.2, weight=3)
def _(c):
    c.key(0.35, ra=(-30, 0, -10), rf=(-50, 0, 0), head=(4, 0, 0))
    # offered to you, palm up; a second beat a little further out; a small nod to close the thought
    c.key(0.8, ra=(-52, 16, -8), rf=(-36, 0, 0), head=(8, 0, -4))
    c.key(1.1, ra=(-50, 18, -8), head=(4, 0, -6))
    c.key(1.6, ra=(-46, 26, -4), rf=(-30, 0, 0), head=(6, 4, -6))
    c.key(2.1, ra=(-50, 18, -8), rf=(-38, 0, 0), head=(10, 0, -2))
    c.key(2.7, ra=(-6, 0, 0), rf=(-6, 0, 0), head=(0, 0, 0))
    c.key(3.2)


@clip("talk_shape_cloud", "Both hands shape a cloud", trigger="talk", length=3.8, weight=2, require=["adult"],
      mirror="free")
def _(c):
    c.key(0.45, ra=(-50, -8, -16), rf=(-44, 0, 0), la=(-50, -8, -16), lf=(-44, 0, 0), head=(10, 0, 0))

    # the hands trace two round billows side by side, the cloud growing as they go; the eyes follow
    def billow(t):
        a = (t - 0.45) / 1.15 * math.tau
        grow = (t - 0.45) / 2.3
        arm = (-50 - 12 * math.sin(a), -8 + 10 * grow + 8 * (1 - math.cos(a)) / 2, -16)
        return dict(ra=arm, la=arm, rf=(-44 + 8 * math.sin(a), 0, 0), lf=(-44 + 8 * math.sin(a), 0, 0),
                    head=(10 - 4 * math.sin(a), 0, 5 * math.sin(a / 2)))
    sampled(c, 0.45, 2.75, billow, step=0.115)
    # and lets it float off: the hands open and the eyes lift after it
    c.key(3.15, ra=(-52, 26, -4), rf=(-24, 0, 0), la=(-52, 26, -4), lf=(-24, 0, 0), head=(-8, 0, 0))
    c.key(3.8)


@clip("talk_hand_heart", "A hand on the heart", trigger="talk", length=3.4, weight=2)
def _(c):
    c.key(0.45, head=(4, 0, 4), **HEART)
    c.key(1.0, head=(8, 0, 8), **HEART, **bowed(6, legs=0.6))
    c.key(1.5, head=(14, 0, 8))
    c.key(2.0, head=(4, 0, 8))
    c.key(2.5, head=(2, 0, 4), **HEART, **bowed(0))
    c.key(3.0, ra=(-6, -6, 0), rf=(-10, 0, 0), head=(0, 0, 0))
    c.key(3.4)


@clip("talk_point_you", "A playful point at you", trigger="talk", length=2.8, weight=2,
      boost={"talking": 2, "manner:flighty": 2})
def _(c):
    c.key(0.35, ra=(-60, -6, -14), rf=(-40, 0, 0), head=(4, 0, 6))
    c.key(0.6, ra=(-82, -8, -16), rf=(14, 0, 0), head=(2, 0, 10), root_pos=(0, 0, -0.6))
    # you! a little wag of the finger, then a giggle in the shoulders
    c.wobble(0.7, 1.5, 3, "ra", 4, base=(-82, -8, -16), axis=1)
    c.key(1.5, head=(-4, 0, 10))
    c.wobble(1.55, 2.1, 6, "ra_pos", 0.4, axis=1)
    c.wobble(1.55, 2.1, 6, "la_pos", 0.4, axis=1)
    c.key(2.2, ra=(-10, 0, 0), rf=(-10, 0, 0), head=(0, 0, 2), root_pos=(0, 0, 0))
    c.key(2.8)


@clip("talk_lean_confide", "Leans in to confide", trigger="talk", length=3.8, weight=2, require=["adult"],
      boost={"talking": 2})
def _(c):
    side = dict(ra=(-56, -20, -16), rf=(-110, 0, 0))
    c.key(0.6, root_pos=(0, 0.2, -1.6), head=(4, -10, 6), **side, **bowed(10, legs=0.6))
    c.key(1.3, head=(6, -12, 8))
    c.key(2.0, head=(4, -10, 6), **side)
    # back again, with a knowing little nod
    c.key(2.5, head=(10, 0, 2), ra=(-24, -10, -6), rf=(-40, 0, 0), root_pos=(0, 0, -0.6), **bowed(2, legs=0.6))
    c.key(2.8, head=(2, 0, 0))
    c.key(3.3, ra=(0, 0, 0), rf=(0, 0, 0), root_pos=(0, 0, 0), **bowed(0))
    c.key(3.8)


@clip("talk_veil_shrug", "A shrug of the veils", trigger="talk", length=2.8, weight=2, mirror="free")
def _(c):
    up = dict(ra=(-6, 50, -8), rf=(-72, 0, 0), la=(-6, 50, -8), lf=(-72, 0, 0), ra_pos=(0, -1.2, 0),
              la_pos=(0, -1.2, 0), right_veil=(16, 0, 18), left_veil=(16, 0, 18), right_veil2=(-10, 0, 0),
              left_veil2=(-10, 0, 0), root_pos=(0, -0.6, 0))
    c.key(0.4, head=(-2, 0, 12), **up)
    c.key(1.1, head=(0, 0, 14), **up)
    # and they drop, the veils settling after the shoulders with a little ripple
    c.key(1.45, ra=(2, 10, -6), rf=(-14, 0, 0), la=(2, 10, -6), lf=(-14, 0, 0), ra_pos=(0, 0.3, 0), la_pos=(0, 0.3, 0),
          head=(6, 0, 0), right_veil=(-2, 0, -4), left_veil=(-2, 0, -4), right_veil2=(8, 0, 0),
          left_veil2=(8, 0, 0), root_pos=(0, 0.3, 0))
    c.key(1.8, right_veil2=(-4, 0, 0), left_veil2=(-4, 0, 0), right_veil3=(6, 0, 0), left_veil3=(6, 0, 0))
    c.key(2.2, ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), ra_pos=(0, 0, 0), la_pos=(0, 0, 0),
          head=(0, 0, 0), right_veil=(0, 0, 0), left_veil=(0, 0, 0), right_veil2=(0, 0, 0), left_veil2=(0, 0, 0),
          right_veil3=(0, 0, 0), left_veil3=(0, 0, 0), root_pos=(0, 0, 0))
    c.key(2.8)


@clip("talk_wistful_up", "A wistful look up at the sky", trigger="talk", length=4.2, weight=1, require=["adult"],
      boost={"manner:restless": 3, "manner:steady": 1.5}, avoid=["manner:busy"])
def _(c):
    c.key(0.8, head=(-20, 14, 6), hair=(16, 0, 0), ra=(-100, 30, 4), rf=(-20, 0, 0), body=(-4, 0, 0),
          rl=(4, 0, 0), ll=(4, 0, 0), right_veil=(10, 0, 10))
    c.key(2.0, head=(-22, 18, 6), ra=(-112, 34, 6), rf=(-16, 0, 0), hair=(18, 0, 0))
    # a breath, and back down to you
    c.key(2.55, ra_pos=(0, -0.6, 0), la_pos=(0, -0.6, 0), head=(-16, 12, 6))
    c.key(3.1, ra_pos=(0, 0.4, 0), la_pos=(0, 0.4, 0), head=(6, 0, 4), hair=(-4, 0, 0), ra=(-20, 10, 0),
          rf=(-20, 0, 0), body=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0), right_veil=(0, 0, 0))
    c.key(3.6, ra_pos=(0, 0, 0), la_pos=(0, 0, 0), head=(0, 0, 0), hair=(0, 0, 0), ra=(0, 0, 0), rf=(0, 0, 0))
    c.key(4.2)


@clip("talk_child_flap", "Flaps the arms as they tell it", trigger="talk", length=2.6, weight=3,
      require=["child"], mirror="free")
def _(c):
    c.key(0.25, ra=(-20, 0, 40), la=(-20, 0, 40), head=(-6, 0, 0))
    c.cycle(0.25, 1.95, 0.4,
            dict(ra=(-20, 0, 66), la=(-20, 0, 66), root_pos=(0, -1.2, 0), head=(-8, 0, 6), rl=(-16, 0, 0),
                 ll=(-16, 0, 0), rs=(24, 0, 0), ls=(24, 0, 0)),
            dict(ra=(-20, 0, 24), la=(-20, 0, 24), root_pos=(0, 0.3, 0), head=(0, 0, -6), rl=(0, 0, 0),
                 ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0)))
    c.key(2.2, ra=(0, 0, 6), la=(0, 0, 6), root_pos=(0, 0, 0), head=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0),
          rs=(0, 0, 0), ls=(0, 0, 0))
    c.key(2.6)


@clip("talk_child_secret", "Cups a hand to whisper a secret", trigger="talk", length=3.2, weight=2,
      require=["child"])
def _(c):
    cup = dict(ra=(-56, -20, -16), rf=(-110, 0, 0), la=(-20, -20, -10), lf=(-40, 0, 0))
    c.key(0.5, root_pos=(0, 0, -1.0), head=(4, -14, 4), **cup, **bowed(8, legs=0.6))
    # anyone listening? a look each way first
    c.key(0.9, head=(4, 14, 4))
    c.key(1.3, head=(4, -14, 4))
    c.key(1.7, head=(6, 0, 6), **cup)
    c.wobble(1.9, 2.5, 6, "ra_pos", 0.4, axis=1)
    c.wobble(1.9, 2.5, 6, "la_pos", 0.4, axis=1)
    c.wobble(1.9, 2.5, 3, "head", 5, base=(6, 0, 6), axis=2)
    c.key(2.7, ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), root_pos=(0, 0, 0), head=(0, 0, 0),
          **bowed(0))
    c.key(3.2)


@clip("talk_child_rock", "Rocks on the air like a little boat", trigger="talk", length=3.0, weight=2,
      require=["child"], boost={"manner:flighty": 2, "manner:restless": 2}, mirror="free")
def _(c):
    c.key(0.3, ra=(-10, 0, 60), la=(-10, 0, 60), head=(-4, 0, 0))
    c.cycle(0.45, 2.45, 1.0,
            dict(root=(0, 0, 20), head=(-4, 0, -10), ra=(-10, 0, 48), la=(-10, 0, 80), rl=(-14, 0, 0)),
            dict(root=(0, 0, -20), head=(-4, 0, 10), ra=(-10, 0, 80), la=(-10, 0, 48), rl=(0, 0, 0),
                 ll=(-14, 0, 0)))
    c.key(2.7, root=(0, 0, 0), head=(0, 0, 0), ra=(0, 0, 6), la=(0, 0, 6), rl=(0, 0, 0), ll=(0, 0, 0))
    c.key(3.0)


# -- listen: while you choose a reply ---------------------------------------------------------------------------

@clip("listen_nod", "Nods attentively", trigger="listen", length=3.8, weight=3)
def _(c):
    c.key(0.5, head=(4, 0, 3), **LOW_CLASP)
    # one slow deep nod, then two small ones
    c.key(1.1, head=(16, 0, 3), hair=(-12, 0, 0))
    c.key(1.6, head=(2, 0, 4), hair=(0, 0, 0))
    c.key(2.1, head=(9, 0, 4))
    c.key(2.35, head=(3, 0, 4))
    c.key(2.6, head=(9, 0, 4))
    c.key(2.9, head=(2, 0, 2), **LOW_CLASP)
    c.key(3.8)


@clip("listen_tilt", "Tilts the head curiously", trigger="listen", length=3.8, weight=3, mirror="free")
def _(c):
    c.key(0.7, head=(-2, 8, 14), body=(0, 0, -2), right_veil=(4, 0, 10), right_veil2=(-6, 0, 0))
    c.key(1.6, head=(-4, 10, 16), right_veil=(6, 0, 12))
    # hm? the other way, a little less
    c.key(2.2, head=(0, -4, -9), body=(0, 0, 2), right_veil=(0, 0, 0), right_veil2=(0, 0, 0),
          left_veil=(4, 0, 8))
    c.key(2.9, head=(2, -4, -10))
    c.key(3.3, head=(2, 0, 0), body=(0, 0, 0), left_veil=(0, 0, 0))
    c.key(3.8)


@clip("listen_chin", "A hand under the chin", trigger="listen", length=4.2, weight=2, require=["adult"])
def _(c):
    chin = dict(ra=(-42, -30, -18), rf=(-112, 0, 0), la=(-26, -40, -18), lf=(-88, 0, 0))
    c.key(0.6, head=(6, 0, -4), **chin)
    # a fingertip taps the chin while they think, eyes up and away; then back to you
    c.wobble(0.8, 1.9, 3, "rf", 6, base=(-112, 0, 0))
    c.key(1.3, head=(-8, 10, -6))
    c.key(1.9, head=(-8, 12, -6))
    c.key(2.4, head=(6, 0, -4))
    c.key(2.8, head=(11, 0, -4))
    c.key(3.2, head=(4, 0, -3), **chin)
    c.key(4.2)


@clip("listen_drift_bob", "Drifts and bobs as they listen", trigger="listen", length=4.4, weight=2,
      boost={"manner:restless": 3}, mirror="free")
def _(c):
    def drift(t):
        e = env(t, 0, 4.4, 0.8)
        return dict(root_pos=(1.6 * sn(t, 4.4) * e, 0.8 * sn(t, 1.47) * e, 0),
                    body=(0, 0, -3 * sn(t, 4.4, 0.08) * e),
                    head=(2 * e, 0, 4 * e + 3 * sn(t, 4.4, 0.15) * e),
                    ra=(-4 * e, 0, 8 * e * sn(t, 2.2)), la=(-4 * e, 0, -8 * e * sn(t, 2.2)),
                    right_veil=(4 * e, 0, 6 * sn(t, 4.4, -0.1) * e), left_veil=(4 * e, 0, -6 * sn(t, 4.4, -0.1) * e))
    sampled(c, 0, 4.4, drift, step=0.2)


@clip("listen_clasp_lean", "Leans in with the hands clasped under the chin", trigger="listen", length=4.0,
      weight=2, require=["adult"], boost={"manner:steady": 1.5})
def _(c):
    under = dict(ra=(-40, -34, -18), rf=(-104, 0, 0), la=(-40, -34, -18), lf=(-104, 0, 0))
    c.key(0.8, head=(-2, 0, 8), root_pos=(0, 0, -1.0), **under, **bowed(9, legs=0.7))
    c.key(2.4, head=(0, 0, 10), **under)
    c.key(2.9, head=(8, 0, 6))
    c.key(3.4, head=(0, 0, 0), root_pos=(0, 0, 0), ra=(-4, 0, 0), rf=(-6, 0, 0), la=(-4, 0, 0), lf=(-6, 0, 0),
          **bowed(0))
    c.key(4.0)


@clip("listen_child_fidget", "Fidgets with a wrist ribbon", trigger="listen", length=3.4, weight=3,
      require=["child"], boost={"manner:busy": 3, "manner:restless": 2})
def _(c):
    hands = dict(ra=(-30, -30, -16), rf=(-70, 0, 0), la=(-34, -26, -16), lf=(-60, 0, 0))
    c.key(0.4, head=(14, -4, 0), **hands)
    c.wobble(0.5, 1.5, 4, "rf", 10, base=(-70, 0, 0))
    c.key(1.7, head=(0, 4, 6))
    c.key(2.1, head=(12, -6, 0))
    c.wobble(2.15, 2.85, 4, "rf", 10, base=(-70, 0, 0))
    c.wave(0.4, 3.0, 1.3, "rl", 14, base=(-6, 0, 0))
    c.wave(0.4, 3.0, 1.3, "ll", 14, base=(-6, 0, 0), phase=0.5)
    c.key(3.0, head=(0, 0, 0), ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0))
    c.key(3.4)


@clip("listen_child_lounge", "Lounges back on the air and kicks", trigger="listen", length=3.6, weight=2,
      require=["child"], mirror="free")
def _(c):
    # the arms draped out along the air behind them, as if along the back of a cloud
    behind = dict(ra=(24, 0, 46), rf=(-26, 0, 0), la=(24, 0, 46), lf=(-26, 0, 0))
    c.key(0.6, root=(-26, 0, 0), head=(16, 0, 6), rl=(-30, 0, 0), ll=(-10, 0, 0), rs=(30, 0, 0), ls=(20, 0, 0),
          **behind)
    c.cycle(0.7, 2.8, 0.9, dict(rl=(-34, 0, 0), rs=(20, 0, 0), ll=(-6, 0, 0), ls=(40, 0, 0)),
            dict(rl=(-6, 0, 0), rs=(40, 0, 0), ll=(-34, 0, 0), ls=(20, 0, 0)))
    c.key(2.8, root=(-26, 0, 0), head=(16, 0, 6), **behind)
    c.key(3.2, root=(0, 0, 0), head=(0, 0, 0), rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0),
          ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0))
    c.key(3.6)
