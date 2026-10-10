package dev.skyfriends.flight;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class GlideTest {
    private static double heading(double[] v) {
        return Math.atan2(v[2], v[0]);
    }

    @Test
    void headingTurnsNoFasterThanTheLimit() {
        double[] v = {0.3, 0, 0};
        double[] want = {-0.3, 0, 0.001};                  // right round behind it
        for (int i = 0; i < 10; i++) {
            double[] next = Glide.steer(v, want, 0.05, 0.01, 0.02);
            assertTrue(Math.abs(Glide.wrap(heading(next) - heading(v))) <= 0.05 + 1e-9);
            v = next;
        }
    }

    @Test
    void aFullTurnTakesArcNotASnap() {
        double[] v = {0.3, 0, 0};
        double[] want = {-0.3, 0, 0.001};
        int ticks = 0;
        while (Math.abs(Glide.wrap(heading(v) - Math.PI)) > 0.05 && ticks < 200) {
            v = Glide.steer(v, want, 0.055, 0.012, 0.02);
            ticks++;
        }
        assertTrue(ticks > 40 && ticks < 80, "turned round in " + ticks + " ticks");
    }

    @Test
    void speedAndClimbEaseTowardWhatIsWanted() {
        double[] v = {0, 0, 0};
        for (int i = 0; i < 100; i++) v = Glide.steer(v, new double[] {0, 0.1, 0.3}, 0.055, 0.012, 0.02);
        assertEquals(0.3, Math.hypot(v[0], v[2]), 1e-6);
        assertEquals(0.1, v[1], 1e-6);
    }

    @Test
    void towardSlowsToAStopOnArrival() {
        double[] far = Glide.toward(new double[] {0, 0, 0}, new double[] {20, 0, 0}, 0.3, 5);
        assertEquals(0.3, far[0], 1e-9);
        double[] near = Glide.toward(new double[] {0, 0, 0}, new double[] {1, 0, 0}, 0.3, 5);
        assertEquals(0.06, near[0], 1e-9);
        double[] there = Glide.toward(new double[] {1, 2, 3}, new double[] {1, 2, 3}, 0.3, 5);
        assertEquals(0, there[0] + there[1] + there[2], 1e-12);
    }
}
