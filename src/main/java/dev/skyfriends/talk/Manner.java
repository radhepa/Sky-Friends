package dev.skyfriends.talk;

/**
 * How a Cirri behaves in the air while you talk to them, from their {@link Personality}. Most hover still in
 * front of you for as long as you like; some can't, by nature.
 */
public enum Manner {
    /** Hovers still in front of you. */
    STEADY,
    /** Keeps a little further off, and drifts back if you crowd them. */
    SHY,
    /** Drifts slowly round you as you talk, but stays. */
    RESTLESS,
    /** After a while excuses themselves and goes back to what they were doing (not with close friends). */
    BUSY,
    /** Darts off for a quick loop now and then, and comes straight back. */
    FLIGHTY
}
