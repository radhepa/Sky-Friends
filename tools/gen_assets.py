"""Writes the mobs' generated assets: models and textures (tools/people/cirri.py, tools/creatures/*.py), spawn
eggs (item definition, model, texture) and their English names, merged into the language file (the block
names come from tools/blocks/gen_blocks.py, which merges too).

  python tools/gen_assets.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "people"))
sys.path.insert(0, os.path.join(HERE, "creatures"))

from mobkit import MOD_ID, ROOT, spawn_egg  # noqa: E402

ASSETS = os.path.join(ROOT, "src", "main", "resources", "assets", MOD_ID)

# id -> (name, egg base colour, egg spots, egg accent)
MOBS = {
    "cirri": ("Cirri", "#a9d9f2", "#e6c15a", "#e3a1af"),
    "cloud_koi": ("Cloud Koi", "#f6f3ee", "#e2553c", "#b9dcf3"),
    "cloud_whale": ("Cloud Whale", "#7596bb", "#eef2f7", "#fff6c8"),
}


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main():
    import cirri
    import cloud_koi
    import cloud_whale
    cirri.build()
    first = True
    for coat in cloud_koi.COATS:
        cloud_koi.build(coat, geometry=first)
        first = False
    cloud_whale.build()
    lang_path = os.path.join(ASSETS, "lang", "en_us.json")
    lang = json.load(open(lang_path, encoding="utf-8")) if os.path.exists(lang_path) else {}
    for mob, (name, base, spots, accent) in MOBS.items():
        egg = f"{mob}_spawn_egg"
        spawn_egg(mob, base, spots, accent)
        write(os.path.join(ASSETS, "items", egg + ".json"), {"model": {"type": "minecraft:model", "model": f"{MOD_ID}:item/{egg}"}})
        write(os.path.join(ASSETS, "models", "item", egg + ".json"),
              {"parent": "minecraft:item/generated", "textures": {"layer0": f"{MOD_ID}:item/{egg}"}})
        lang[f"entity.{MOD_ID}.{mob}"] = name
        lang[f"item.{MOD_ID}.{egg}"] = f"{name} Spawn Egg"
    lang[f"itemGroup.{MOD_ID}"] = "Sky Friends"
    write(lang_path, dict(sorted(lang.items())))
    print("assets written:", ", ".join(MOBS))


if __name__ == "__main__":
    main()
