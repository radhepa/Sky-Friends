package dev.skyfriends.client.anim;

import dev.skyfriends.anim.Clip;

/**
 * What one person is acting out this frame: up to three clips (the activity, a reaction, and an activity fading
 * out), each with its time, weight and side. Lives in the render state; the director fills it, the poser reads it.
 */
public final class Pose {
    public String species;
    public final Layer[] layers = {new Layer(), new Layer(), new Layer()};
    /** Arms that hold an item keep their vanilla pose (Piglins with a crossbow or a sword). */
    public boolean holdingRight, holdingLeft;

    public boolean any() {
        for (Layer l : layers) if (l.active()) return true;
        return false;
    }

    public void clear() {
        for (Layer l : layers) l.clear();
    }

    public static final class Layer {
        public Clip clip;
        public float time, weight, lower = 1;
        public boolean mirror;

        public void set(Clip clip, float time, float weight, boolean mirror, float lower) {
            this.clip = clip;
            this.time = time;
            this.weight = weight;
            this.mirror = mirror;
            this.lower = lower;
        }

        public void clear() {
            clip = null;
            weight = 0;
        }

        public boolean active() {
            return clip != null && weight > 0;
        }
    }
}
