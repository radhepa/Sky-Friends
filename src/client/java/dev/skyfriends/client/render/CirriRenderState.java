package dev.skyfriends.client.render;

import dev.skyfriends.client.EmoteBubbles;
import dev.skyfriends.client.anim.Pose;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;

/** What the Cirri model needs each frame. */
public class CirriRenderState extends LivingEntityRenderState {
    /** 0 hovering upright .. 1 stretched out at full cruise; -1..1 banking (right turn positive) and climbing. */
    public float flight, bank, climb;
    /** The living eyes: a per-person seed, a feminine face, and the gaze toward a nearby camera (Village Friends' eye contact). */
    public int motionSeed;
    public boolean feminine;
    public float eyeLookX, eyeLookY, attention;
    /** Asleep (eyes shut, curled up) or at work; which model and texture. */
    public boolean sleeping, working, female;
    public String texture = "cirri_f_0_dawn";
    /** The clips they are acting out (docs/ANIMATIONS.md), and the bubble over their head, if any. */
    public final Pose pose = new Pose();
    public EmoteBubbles.Bubble bubble;
    public float bubbleAge;
}
