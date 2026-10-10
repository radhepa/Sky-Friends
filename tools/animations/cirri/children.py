from kit import clip
import math

# Cirri children at play in the air: tumbling, spinning, chasing koi, showing off, sulking. A child's model is
# small with a big head and short arms and veils; the pack's root turns about height 13, which on a child is
# about its middle already, so its somersaults need hardly any lift. The live hovering pose is under every clip
# (arms afloat about 20 degrees out with soft elbows, soft knees).

HIP = 13.0   # the pack's hip height: the root turns about it
MID = 12.0   # a child's middle (between bun and toes)
CHILD = ["child"]
FLIGHTY = {"manner:flighty": 3}


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
    middle instead of the pack's hip height."""
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
    """One whole turn of the body between t0 and t1. Euler angles can't come back round to zero by a smooth path,
    so the angle runs on to 360 and steps back to 0 a ten-thousandth of a second later, when the body is upright
    again in the very same orientation (and at rest, so nothing shows)."""
    def pose(t):
        angle = sign * 360 * ease((t - t0) / (t1 - t0))
        rot, pos = turn_pose(angle, axis, mid)
        if extra:
            rot = tuple(r + e for r, e in zip(rot, extra(t, angle)))
        return dict(root=rot, root_pos=pos)
    sampled(c, t0, t1, pose, step)
    c.key(t1 + 0.0001, root=(0, 0, 0), root_pos=(0, 0, 0))


def lean(c, t, angle, **pose):
    """Tip the whole body forward (+) or back (-) about its middle."""
    rot, pos = turn_pose(angle, 0)
    c.key(t, root=rot, root_pos=pos, **pose)


TUCK = dict(rl=(-80, 0, 0), ll=(-80, 0, 0), rs=(100, 0, 0), ls=(100, 0, 0))
HUG_SHINS = dict(ra=(-50, -25, -20), la=(-50, -25, -17), rf=(-50, 0, 0), lf=(-50, 0, 0))
CROSSED = dict(ra=(-35, -50, -20), rf=(-80, 0, 0), la=(-35, -50, -17), lf=(-88, 0, 0))
# a child's arms are short and its head big: hands over the eyes reach well forward, and arms thrown up go
# out wide (straight up, they hide behind the head)
EYES = dict(ra=(-105, -30, -20), rf=(-10, 0, 0), la=(-105, -30, -17), lf=(-15, 0, 0))
V_UP = dict(ra=(-10, 0, 118), la=(-10, 0, 120), rf=(29, 0, 0), lf=(20, 0, 0))
ARMS_REST = dict(ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0))
LEGS_REST = dict(rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0))


@clip("kid_somersault", "Tumbles head over heels", length=2.8, weight=3, require=CHILD, boost=FLIGHTY,
      mirror="never")
def _(c):
    # a quick tight somersault, knees hugged, and out of it with arms flung wide
    c.key(0.3, head=(20, 0, 0), **TUCK, **HUG_SHINS)
    c.key(1.9, head=(20, 0, 0), **TUCK, **HUG_SHINS)
    full_turn(c, 0.3, 2.0, 0)
    c.key(1.2, right_veil=(40, 0, 20), left_veil=(40, 0, 20), hair=(30, 0, 0))
    c.key(2.25, ra=(-20, 0, 60), la=(-20, 0, 60), rf=(10, 0, 0), lf=(10, 0, 0), head=(-12, 0, 0),
          right_veil=(-10, 0, 20), left_veil=(-10, 0, 20), hair=(-10, 0, 0), **LEGS_REST)
    c.key(2.8)


@clip("kid_show_off_loop", "Shows off a loop", length=3.6, weight=2, require=CHILD, avoid=["manner:shy"],
      boost=FLIGHTY, mirror="never")
def _(c):
    # watch this! A backward loop, arms up the whole way round, and a ta-da at the end
    c.key(0.4, head=(6, 0, 0), ra=(-20, 0, 30), la=(-20, 0, 30), root_pos=(0, 0.8, 0), rl=(-20, 0, 0),
          ll=(-20, 0, 0))
    c.key(0.75, head=(-20, 0, 0), rl=(10, 0, 0), ll=(10, 0, 0), rs=(-10, 0, 0), ls=(-10, 0, 0), **V_UP)
    full_turn(c, 0.6, 2.2, 0, sign=-1)
    c.key(1.4, right_veil=(-30, 0, 30), left_veil=(-30, 0, 30), hair=(-30, 0, 0))
    c.key(2.2, head=(-10, 0, 0), **V_UP)
    # ta-da: a bounce with the arms up in a V, and a proud little wiggle
    c.key(2.45, root_pos=(0, -1.5, 0), ra=(-20, 0, 112), la=(-20, 0, 112), head=(-14, 0, 6),
          right_veil=(0, 0, 25), left_veil=(0, 0, 25), hair=(10, 0, 0), **LEGS_REST)
    c.key(2.7, root_pos=(0, 0, 0), head=(-10, 0, -6))
    c.key(2.95, head=(-10, 0, 6))
    c.key(3.2, ra=(0, 0, 20), la=(0, 0, 20), rf=(0, 0, 0), lf=(0, 0, 0), head=(0, 0, 0), right_veil=(0, 0, 0),
          left_veil=(0, 0, 0), hair=(0, 0, 0))
    c.key(3.6)


@clip("kid_tumble_roll", "Tumbles over sideways", length=3.2, weight=2, require=CHILD, boost=FLIGHTY, mirror="free")
def _(c):
    # curled up small and rolled over sideways like a ball, then a wobbly uncurl
    c.key(0.35, head=(20, 0, 0), **TUCK, **HUG_SHINS)
    c.key(1.7, head=(20, 0, 0), **TUCK, **HUG_SHINS)
    full_turn(c, 0.3, 1.85, 2)
    c.key(2.1, ra=(0, 0, 40), la=(0, 0, 45), rf=(0, 0, 0), lf=(0, 0, 0), head=(-6, 0, 0), **LEGS_REST)
    c.wobble(2.0, 2.9, 3.5, "root", 6, axis=2, decay=0.7)
    c.wobble(2.0, 2.9, 3.5, "head", 8, axis=2, decay=0.6)
    c.key(2.8, ra=(0, 0, 0), la=(0, 0, 0))
    c.key(3.2)


@clip("kid_pretend_swim", "Pretend-swims", length=3.8, weight=2, require=CHILD, mirror="free")
def _(c):
    # tips forward and swims hard on nothing: big breaststrokes, frog kicks, cheeks puffed (head bobbing)
    reach = dict(ra=(-150, -6, -20), la=(-150, -6, -17), rf=(29, 0, 0), lf=(20, 0, 0))
    sweep = dict(ra=(-90, 60, 15), la=(-90, 60, 15), rf=(15, 0, 0), lf=(10, 0, 0))
    pull = dict(ra=(-40, -30, -20), la=(-40, -30, -17), rf=(-80, 0, 0), lf=(-85, 0, 0))
    kick_in = dict(rl=(-50, 0, 20), ll=(-50, 0, 20), rs=(90, 0, 0), ls=(90, 0, 0))
    kick_out = dict(rl=(10, 0, 4), ll=(10, 0, 4), rs=(-10, 0, 0), ls=(-10, 0, 0))
    lean(c, 0.5, 35, head=(-30, 0, 0), hair=(-10, 0, 0), **pull, **kick_in)
    for t0 in (0.5, 1.6):
        c.key(t0 + 0.3, head=(-34, 0, 0), **reach, **kick_out)
        c.key(t0 + 0.65, head=(-26, 0, 0), **sweep)
        c.key(t0 + 1.0, head=(-30, 0, 0), **pull, **kick_in)
    lean(c, 2.8, 35)
    lean(c, 3.3, 0, head=(0, 0, 0), hair=(0, 0, 0), **ARMS_REST, **LEGS_REST)
    c.key(3.8)


@clip("kid_kick_legs", "Kicks the legs", length=3.2, weight=2, require=CHILD, mirror="free")
def _(c):
    # sitting on nothing and kicking both legs, head bobbing along to the kicks
    c.key(0.4, rl=(-50, 0, 0), ll=(-50, 0, 0), rs=(50, 0, 0), ls=(50, 0, 0), ra=(20, 0, -10), la=(20, 0, -10),
          rf=(10, 0, 0), lf=(10, 0, 0))
    for i in range(6):
        t = 0.6 + i * 0.35
        s = 1 if i % 2 else -1
        c.key(t, rs=(50 + 40 * s, 0, 0), ls=(50 - 40 * s, 0, 0), head=(4, 0, 5 * s), root=(0, 0, 2 * s))
    c.key(2.7, rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0), ra=(0, 0, 0), la=(0, 0, 0), rf=(0, 0, 0),
          lf=(0, 0, 0), head=(0, 0, 0), root=(0, 0, 0))
    c.key(3.2)


@clip("kid_dizzy_spin", "Spins till dizzy", length=4.2, weight=2, require=CHILD, boost=FLIGHTY, mirror="free")
def _(c):
    # round and round with arms out... and then the whole sky keeps going round without them
    c.key(0.3, ra=(-8, 0, 66), la=(-6, 0, 70), rf=(25, 0, 0), lf=(18, 0, 0), head=(-10, 0, 0))
    c.key(1.4, ra=(-8, 0, 66), la=(-6, 0, 70), head=(-10, 0, 0))
    full_turn(c, 0.25, 1.5, 1)

    def dizzy(t):
        e = env(t, 1.55, 3.9, 0.4)
        return dict(root=(3 * sn(t, 0.9, 0.25) * e, 0, 9 * sn(t, 0.9) * e),
                    head=(6 * sn(t, 0.9, 0.25) * e, 10 * sn(t, 1.2) * e, -12 * sn(t, 0.9, 0.1) * e))
    sampled(c, 1.55, 3.9, dizzy, step=0.1)   # (starts after the turn's last key, so it can't undo the turn)
    c.key(1.8, ra=(-20, 0, 40), la=(-20, 0, 40), rf=(0, 0, 0), lf=(0, 0, 0))
    c.wobble(1.8, 3.4, 1.1, "ra", 14, base=(-20, 0, 40), axis=2)
    c.wobble(1.8, 3.4, 1.1, "la", -14, base=(-20, 0, 40), axis=2)
    c.key(3.8, ra=(0, 0, 0), la=(0, 0, 0))
    c.key(4.2)


@clip("kid_peekaboo", "Peekaboo with the veils", length=4.0, weight=2, require=CHILD)
def _(c):
    # hands over the eyes behind the veils drawn round to the front... and boo! Arms and veils flung wide
    hide = dict(right_veil=(-100, -26, -20), left_veil=(-100, -26, -20), right_veil2=(80, 0, 0),
                left_veil2=(80, 0, 0), head=(10, 0, 0), **EYES)
    boo = dict(ra=(-40, 0, 110), la=(-40, 0, 110), rf=(25, 0, 0), lf=(20, 0, 0), right_veil=(-10, 0, 60),
               left_veil=(-10, 0, 60), right_veil2=(0, 0, 0), left_veil2=(0, 0, 0), head=(-14, 0, 0))
    c.key(0.6, **hide)
    c.key(1.3, **hide)
    c.key(1.5, root_pos=(0, -2, 0), **boo)
    c.key(1.75, root_pos=(0, 0, 0))
    c.key(2.0, **boo)
    c.key(2.5, **hide)
    c.key(2.9, **hide)
    c.key(3.1, root_pos=(0, -2, 0), **boo)
    c.key(3.35, root_pos=(0, 0, 0), head=(-10, 0, 8))
    c.key(3.6, right_veil=(0, 0, 0), left_veil=(0, 0, 0), head=(0, 0, 0), **ARMS_REST)
    c.key(4.0)


@clip("kid_koi_chase", "Chases a koi", length=3.8, weight=2, require=CHILD)
def _(c):
    # a koi darts by: a lunge and a two-handed grab to the left - missed! - and to the right - got it? Empty hands
    grab_l = dict(ra=(-80, -50, -20), rf=(-10, 0, 0), la=(-80, 10, 10), lf=(0, 0, 0))
    clap_l = dict(ra=(-80, -40, -20), rf=(-30, 0, 0), la=(-80, -20, -17), lf=(-30, 0, 0))
    grab_r = dict(ra=(-80, 10, 10), rf=(0, 0, 0), la=(-80, -50, -17), lf=(-10, 0, 0))
    clap_r = dict(ra=(-80, -20, -20), rf=(-30, 0, 0), la=(-80, -40, -17), lf=(-30, 0, 0))
    c.key(0.5, head=(4, -30, 0), root=(10, -25, 0), root_pos=(1.5, 0, -1.5), **grab_l)
    c.key(0.75, head=(8, -30, 0), root=(14, -28, 0), root_pos=(2.5, 0.5, -2.5), **clap_l)
    c.key(1.3, head=(2, 30, 0), root=(10, 25, 0), root_pos=(-1.5, 0, -1.5), **grab_r)
    c.key(1.55, head=(8, 30, 0), root=(14, 28, 0), root_pos=(-2.5, 0.5, -2.5), **clap_r)
    # a peek into the cupped hands...
    c.key(2.2, head=(28, 0, 0), root=(4, 0, 0), root_pos=(0, 0, 0), ra=(-55, -35, -20), rf=(-55, 0, 0),
          la=(-55, -35, -17), lf=(-60, 0, 0))
    c.key(2.7, head=(30, 0, 8))
    # ...nothing. Hands open, a puzzled tilt
    c.key(3.0, head=(-6, 0, -14), root=(0, 0, 0), ra=(-30, 40, 20), rf=(-20, 0, 0), la=(-30, 40, 20),
          lf=(-20, 0, 0))
    c.key(3.4, head=(0, 0, 0), **ARMS_REST)
    c.key(3.8)


@clip("kid_bird_flap", "Flaps like a bird", length=3.4, weight=2, require=CHILD, mirror="free")
def _(c):
    # a joke: Cirri don't flap. Big silly flaps anyway, bobbing up and down with them, then a fit of giggles
    up = dict(ra=(0, 0, 100), la=(0, 0, 100), rf=(25, 0, 0), lf=(20, 0, 0), root_pos=(0, -1.6, 0), head=(-8, 0, 0))
    down = dict(ra=(0, 0, 20), la=(0, 0, 20), rf=(10, 0, 0), lf=(10, 0, 0), root_pos=(0, 0.6, 0), head=(6, 0, 0))
    c.key(0.3, rl=(-30, 0, 0), ll=(-30, 0, 0), rs=(40, 0, 0), ls=(40, 0, 0))
    c.cycle(0.3, 2.3, 0.5, down, up, end_on="a")
    c.key(2.3, rl=(-30, 0, 0), ll=(-30, 0, 0), rs=(40, 0, 0), ls=(40, 0, 0))
    c.wobble(2.4, 3.1, 6, "root", 3, axis=2, decay=0.5)
    c.wobble(2.4, 3.1, 6, "head", 6, base=(10, 0, 0), axis=0, decay=0.5)
    c.key(2.6, ra=(-40, -40, -20), rf=(-60, 0, 0), la=(-40, -40, -17), lf=(-65, 0, 0), root_pos=(0, 0, 0))
    c.key(3.0, ra=(0, 0, 0), rf=(0, 0, 0), la=(0, 0, 0), lf=(0, 0, 0), **LEGS_REST)
    c.key(3.4)


@clip("kid_sulk", "Sulks with arms crossed", length=4.6, weight=1, require=CHILD, mirror="free")
def _(c):
    # arms folded, turned away with the chin down; a huff; one cross little kick
    c.key(0.6, root=(0, -20, 0), head=(14, -30, 0), **CROSSED)
    c.key(1.4, root_pos=(0, -0.8, 0), head=(4, -32, 0))
    c.key(1.7, root_pos=(0, 0.4, 0), head=(18, -30, 0))
    c.key(2.2, root_pos=(0, 0, 0))
    c.key(2.6, rl=(-30, 0, 0), rs=(0, 0, 0))
    c.key(2.8, rl=(10, 0, 0), rs=(30, 0, 0))
    c.key(3.1, rl=(0, 0, 0), rs=(0, 0, 0), head=(16, -26, 4))
    c.key(3.6, root=(0, -20, 0), head=(14, -30, 0), **CROSSED)
    c.key(4.1, root=(0, 0, 0), head=(0, 0, 0), **ARMS_REST)
    c.key(4.6)


@clip("kid_yawn", "Yawns and rubs the eyes", length=3.8, weight=2, require=CHILD, mirror="free")
def _(c):
    # a great big yawn with the arms up and the head back, then two little fists rubbing the eyes
    c.key(0.8, head=(-24, 0, 0), hair=(20, 0, 0), root_pos=(0, -0.8, 0), **V_UP)
    c.key(1.5, head=(-26, 0, 4), root_pos=(0, -1, 0))
    c.key(2.0, head=(14, 0, 0), hair=(0, 0, 0), root_pos=(0, 0, 0), **EYES)
    c.wobble(2.0, 3.0, 5, "ra", 6, base=EYES["ra"], axis=1)
    c.wobble(2.0, 3.0, 5, "la", 6, base=EYES["la"], axis=1)
    c.key(3.0, **EYES)
    c.key(3.4, head=(0, 0, 0), **ARMS_REST)
    c.key(3.8)


@clip("kid_wave_at_nothing", "Waves at nothing", length=3.2, weight=2, require=CHILD)
def _(c):
    # a big happy wave up at the sky, bouncing; at a cloud, or a bird, or nobody at all
    # (the upper arm out to the side, the forearm standing up beside the big head, wagging)
    c.key(0.4, ra=(-76, 90, -20), rf=(-60, 0, 0), head=(-18, 10, 0), hair=(14, 0, 0))
    c.wobble(0.4, 2.2, 2.6, "ra", 22, base=(-76, 90, -20), axis=0)
    c.wobble(0.4, 2.2, 1.3, "root_pos", 0.8, base=(0, -0.6, 0), axis=1)
    c.key(2.4, ra=(-76, 90, -20), head=(-14, 10, 10))
    c.key(2.8, ra=(0, 0, 0), rf=(0, 0, 0), head=(0, 0, 0), hair=(0, 0, 0), root_pos=(0, 0, 0))
    c.key(3.2)


@clip("kid_play_bounce", "Bounces with excitement", length=3.0, weight=4, require=["child", "routine:play"],
      mirror="free")
def _(c):
    # can't keep still: bounce, bounce, bounce, knees tucking up and fists pumping
    up = dict(root_pos=(0, -3, 0), rl=(-40, 0, 0), ll=(-40, 0, 0), rs=(70, 0, 0), ls=(70, 0, 0),
              ra=(-60, -20, -10), la=(-60, -20, -10), rf=(-90, 0, 0), lf=(-90, 0, 0), head=(-12, 0, 0))
    down = dict(root_pos=(0, 0.5, 0), rl=(0, 0, 0), ll=(0, 0, 0), rs=(0, 0, 0), ls=(0, 0, 0),
                ra=(-30, -20, -10), la=(-30, -20, -10), rf=(-60, 0, 0), lf=(-60, 0, 0), head=(4, 0, 0))
    c.cycle(0.2, 2.6, 0.6, down, up, end_on="a")
    c.key(3.0)


@clip("kid_follow_bob", "Bobs along behind", length=4.4, weight=4, require=["child", "routine:follow"],
      mirror="free")
def _(c):
    # bobbing along after a grown-up, looking at everything: that cloud, that bird, the ground ever so far down
    def pose(t):
        e = env(t, 0, 4.4, 0.6)
        return dict(root_pos=(0, 0.8 * sn(t, 1.1) * e, 0), root=(0, 0, 3 * sn(t, 2.2) * e),
                    rl=(-10 * sn(t, 1.1) * e, 0, 0), ll=(-10 * sn(t, 1.1, 0.5) * e, 0, 0),
                    ra=(8 * sn(t, 2.2) * e, 0, 6 * e), la=(-8 * sn(t, 2.2) * e, 0, 6 * e))
    sampled(c, 0, 4.4, pose, step=0.11)
    c.key(0.8, head=(-14, 30, 0))
    c.key(1.6, head=(-10, 26, 6))
    c.key(2.3, head=(4, -28, 0))
    c.key(3.0, head=(22, -20, 0))
    c.key(3.7, head=(4, 0, 0))
    c.key(4.4)
