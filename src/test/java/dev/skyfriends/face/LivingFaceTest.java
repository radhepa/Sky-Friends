package dev.skyfriends.face;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.UUID;
import org.junit.jupiter.api.Test;

class LivingFaceTest {
    @Test
    void blinksAreShortAndEveryFiveToEightSeconds() {
        for (int seed : new int[] {1, 5131, -77, 0x51A7E5, 123456789}) {
            int period = LivingFace.blinkPeriod(seed);
            assertTrue(period >= 97 && period < 164, "blink period " + period);
            int closedTicks = 0, blinks = 0;
            boolean wasClosed = false;
            for (int t = 0; t < 20 * 60; t++) {
                float b = LivingFace.blink(t, seed);
                assertTrue(b >= 0 && b <= 1, "blink amount " + b);
                boolean closed = b > 0.9F;
                if (closed) closedTicks++;
                if (closed && !wasClosed) blinks++;
                wasClosed = closed;
            }
            assertTrue(blinks >= 6 && blinks <= 16, "blinks in a minute: " + blinks);
            assertTrue(closedTicks < 20 * 60 / 10, "eyes shut too long: " + closedTicks);
        }
    }

    @Test
    void lashSweepsFromTheTopOfTheEyeToItsBottom() {
        for (LivingFace.EyeStyle style : LivingFace.EyeStyle.values()) {
            assertEquals(LivingFace.eyeTop(style), LivingFace.lashBottom(style, 0), 1e-6);
            assertEquals(LivingFace.EYE_BOTTOM, LivingFace.lashBottom(style, 1), 1e-6);
            assertTrue(LivingFace.browTop(style) + 0.55F < LivingFace.eyeTop(style) - 1, "brows clear of the lash line");
        }
    }

    @Test
    void stylesAndFacesAreSplitAboutEvenly() {
        int starlit = 0, feminine = 0, n = 2000;
        for (int i = 0; i < n; i++) {
            int seed = LivingFace.seed(new UUID(i * 0x9E3779B97F4A7C15L, ~i * 0xC2B2AE3D27D4EB4FL));
            if (LivingFace.eyeStyle(seed) == LivingFace.EyeStyle.STARLIT) starlit++;
            if (LivingFace.feminine(seed)) feminine++;
        }
        assertTrue(Math.abs(starlit - n / 2) < n / 10, "starlit " + starlit);
        assertTrue(Math.abs(feminine - n / 2) < n / 10, "feminine " + feminine);
    }

    @Test
    void glancesStaySmall() {
        for (int t = 0; t < 5000; t += 7) assertTrue(Math.abs(LivingFace.glance(t, 42)) <= 0.18F + 1e-6);
    }
}
