package dev.skyfriends;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.sounds.SoundEvent;

/** The mod's sound events (assets/skyfriends/sounds.json; every sound is synthesized by tools/sounds/synth.py). */
public final class SkySounds {
    private SkySounds() {}

    public static final SoundEvent CIRRI_FEMALE_HUM = event("cirri.female.hum");
    public static final SoundEvent CIRRI_MALE_HUM = event("cirri.male.hum");
    public static final SoundEvent CIRRI_CHILD_HUM = event("cirri.child.hum");
    public static final SoundEvent CIRRI_FEMALE_GREET = event("cirri.female.greet");
    public static final SoundEvent CIRRI_MALE_GREET = event("cirri.male.greet");
    public static final SoundEvent CIRRI_CHILD_GREET = event("cirri.child.greet");
    public static final SoundEvent CIRRI_FEMALE_HURT = event("cirri.female.hurt");
    public static final SoundEvent CIRRI_MALE_HURT = event("cirri.male.hurt");
    public static final SoundEvent CIRRI_CHILD_HURT = event("cirri.child.hurt");
    public static final SoundEvent CIRRI_FEMALE_DEATH = event("cirri.female.death");
    public static final SoundEvent CIRRI_MALE_DEATH = event("cirri.male.death");
    public static final SoundEvent CIRRI_CHILD_DEATH = event("cirri.child.death");
    public static final SoundEvent CIRRI_SLEEP = event("cirri.sleep");
    public static final SoundEvent WIND_HARP = event("wind_harp.play");
    public static final SoundEvent WINDSONG_FLUTE = event("windsong_flute.play");
    public static final SoundEvent WIND_CHIME = event("wind_chime.ring");
    public static final SoundEvent WIND_STONE_LIFT = event("wind_stone.lift");
    public static final SoundEvent CLOUD_WHALE_SONG = event("cloud_whale.song");
    public static final SoundEvent CLOUD_WHALE_HURT = event("cloud_whale.hurt");
    public static final SoundEvent CLOUD_WHALE_DEATH = event("cloud_whale.death");
    public static final SoundEvent CLOUD_KOI_FLUTTER = event("cloud_koi.flutter");

    private static SoundEvent event(String name) {
        var id = SkyFriends.id(name);
        return Registry.register(BuiltInRegistries.SOUND_EVENT, id, SoundEvent.createVariableRangeEvent(id));
    }

    /** Loads the class (the fields above register everything). */
    public static void register() {}
}
