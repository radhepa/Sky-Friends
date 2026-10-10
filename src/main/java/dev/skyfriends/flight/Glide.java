package dev.skyfriends.flight;

/**
 * How a Cirri's velocity follows where it wants to go: its heading turns toward the wanted heading at
 * a limited rate, so it flies in long arcs instead of snapping round, and it slows a little into a
 * sharp turn. Speed and climb ease toward the wanted values. Pure maths (blocks per tick, radians),
 * no game classes, so it is unit-tested.
 */
public final class Glide {
    private Glide() {}

    /**
     * One tick of steering.
     *
     * @param v       current velocity {x, y, z}
     * @param want    wanted velocity {x, y, z}
     * @param turn    most the heading may turn this tick (radians)
     * @param accel   most the horizontal speed may change this tick
     * @param climb   most the vertical speed may change this tick
     * @return the new velocity
     */
    public static double[] steer(double[] v, double[] want, double turn, double accel, double climb) {
        double speed = Math.hypot(v[0], v[2]);
        double wantSpeed = Math.hypot(want[0], want[2]);
        double heading = speed > 1.0E-4 ? Math.atan2(v[2], v[0]) : Math.atan2(want[2], want[0]);
        double wanted = wantSpeed > 1.0E-4 ? Math.atan2(want[2], want[0]) : heading;
        double off = wrap(wanted - heading);
        heading += clamp(off, -turn, turn);
        // a sharp turn costs speed: up to half of it when turning right round
        double target = wantSpeed * (1.0 - 0.5 * Math.min(1.0, Math.abs(off) / Math.PI));
        double newSpeed = approach(speed, target, accel);
        double vy = approach(v[1], want[1], climb);
        return new double[] {Math.cos(heading) * newSpeed, vy, Math.sin(heading) * newSpeed};
    }

    /** The wanted velocity toward a point: full speed until {@code slowWithin} blocks out, then easing to a stop on it. */
    public static double[] toward(double[] from, double[] to, double speed, double slowWithin) {
        double dx = to[0] - from[0], dy = to[1] - from[1], dz = to[2] - from[2];
        double dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (dist < 1.0E-6) return new double[] {0, 0, 0};
        double s = speed * Math.min(1.0, dist / Math.max(1.0E-6, slowWithin));
        return new double[] {dx / dist * s, dy / dist * s, dz / dist * s};
    }

    /** Angle in (-PI, PI]. */
    public static double wrap(double a) {
        a %= Math.PI * 2;
        if (a > Math.PI) a -= Math.PI * 2;
        if (a <= -Math.PI) a += Math.PI * 2;
        return a;
    }

    public static double approach(double value, double target, double step) {
        return value < target ? Math.min(target, value + step) : Math.max(target, value - step);
    }

    static double clamp(double v, double lo, double hi) {
        return Math.max(lo, Math.min(hi, v));
    }
}
