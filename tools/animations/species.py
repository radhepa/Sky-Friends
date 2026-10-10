"""The Cirri's animation pack: the models (looks) it must fit, and the tags clips may use."""
MOD_ID = "skyfriends"
MIN_CLIPS = 60
GEOMETRY_DIRS = ["src/client/resources/assets/skyfriends/geometry"]

SPECIES = {
    "cirri": {"name": "Cirri", "looks": ["cirri", "cirri_male", "cirri_child"]},
}

JOBS = {
    "cirri": ["harpist", "weaver", "gardener", "bellkeeper", "lamplighter", "skymerchant", "windkeeper"],
}
MANNERS = ["steady", "shy", "restless", "busy", "flighty"]
ROUTINES = ["work", "gather", "soar", "chat", "evensong", "escort", "shelter", "idle", "play", "follow"]

# adult/child: age; social: a chat partner is near; talking: in a conversation with the player;
# job:<job>: their job (children have none); manner:<manner>: how they behave while you talk (their personality);
# working: at their workplace in working hours; routine:<routine>: what they are doing (evensong, chat, play...)
TAGS = {
    "common": {"adult", "child", "social", "talking", "working"} | {"manner:" + m for m in MANNERS}
              | {"routine:" + r for r in ROUTINES},
}
for _s, _jobs in JOBS.items():
    TAGS[_s] = set(TAGS.get(_s, ())) | {"job:" + j for j in _jobs}

# a texture to show each look in (tools/animations/sheet.py)
TEXTURES = {"cirri": "cirri_f_0_dawn", "cirri_male": "cirri_m_1_noon", "cirri_child": "cirri_child_f_0"}
