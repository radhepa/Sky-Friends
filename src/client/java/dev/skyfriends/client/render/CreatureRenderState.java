package dev.skyfriends.client.render;

import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;

/** What the sky creatures' models need: the swim phase, and which texture. */
public class CreatureRenderState extends LivingEntityRenderState {
    public float phase;
    /** The partial tick this state was made for (to blend the creatures' own counters). */
    public float delta;
    public String texture = "";
}
