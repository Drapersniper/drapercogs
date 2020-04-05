# -*- coding: utf-8 -*-
# Standard Library
import json

from pathlib import Path

# Cog Dependencies
from edit_me import *
from makers import ItemMaker, MonsterMaker, PetMaker

# ----------------------------------------- Logic and Code -------------------------------------------------------------
# Don't Edit any of this .... The logic can be found in `makers.py`


def main():
    appdir: Path = Path.cwd()
    print(f"Theme will be saved in: {appdir.resolve()}")

    # Folders
    theme_folder: Path = appdir / theme_name
    theme_folder.mkdir(parents=True, exist_ok=True)

    # Files
    pets_fp: Path = theme_folder / "pets.json"
    tr_common_fp: Path = theme_folder / "tr_common.json"
    tr_rare_fp: Path = theme_folder / "tr_rare.json"
    tr_epic_fp: Path = theme_folder / "tr_epic.json"
    tr_legendary_fp: Path = theme_folder / "tr_legendary.json"
    monster_fp: Path = theme_folder / "monsters.json"
    attribs_fp: Path = theme_folder / "attribs.json"

    locations_fp: Path = theme_folder / "locations.json"
    raisins_fp: Path = theme_folder / "raisins.json"
    threatee_fp: Path = theme_folder / "threatee.json"

    for f in [
        pets_fp,
        attribs_fp,
        monster_fp,
        locations_fp,
        raisins_fp,
        threatee_fp,
        tr_common_fp,
        tr_rare_fp,
        tr_epic_fp,
        tr_legendary_fp,
    ]:
        f.touch()
    # -------------------------- PETS --------------------------
    with pets_fp.open("r+", encoding="utf-8") as file:
        print(f"Generating: {pets_fp.resolve()}")
        existing_data = file.read() or "{}"
        existing_data = json.loads(existing_data)
        data = PetMaker.gen_pets(pet_count, pet_names, pet_modifiers, existing_data=existing_data)
        data = json.dumps(data, sort_keys=True, indent=4)
        file.seek(0)
        file.write(data)
        file.truncate()
        file.close()

    # -------------------------- ITEMS --------------------------
    for index, item_path in enumerate(
        [tr_common_fp, tr_rare_fp, tr_epic_fp, tr_legendary_fp], start=1
    ):
        with item_path.open("r+", encoding="utf-8") as file:
            print(f"Generating: {item_path.resolve()}")
            existing_data = file.read() or "{}"
            existing_data = json.loads(existing_data)
            data = ItemMaker.gen_items(
                index,
                item_count,
                item_slots,
                item_modifier,
                item_material,
                existing_data=existing_data,
            )
            data = json.dumps(data, sort_keys=True, indent=4)
            file.seek(0)
            file.write(data)
            file.truncate()
            file.close()
    # -------------------------- Monsters --------------------------
    with monster_fp.open("r+", encoding="utf-8") as file:
        print(f"Generating: {monster_fp.resolve()}")
        existing_data = file.read() or "{}"
        existing_data = json.loads(existing_data)
        data = MonsterMaker.gen_monsters(
            monster_count,
            monster_names,
            monster_modifiers,
            existing_data=existing_data,
            any_can_be_boss=any_monster_can_be_a_boss,
        )
        data = json.dumps(data, sort_keys=True, indent=4)
        file.seek(0)
        file.write(data)
        file.truncate()
        file.close()
    # -------------------------- Monsters  Attributes--------------------------
    with attribs_fp.open("r+", encoding="utf-8") as file:
        print(f"Generating: {attribs_fp.resolve()}")
        existing_data = file.read() or "{}"
        existing_data = json.loads(existing_data)
        existing_data.update(monster_attributes)
        data = existing_data
        data = json.dumps(data, sort_keys=True, indent=4)
        file.seek(0)
        file.write(data)
        file.truncate()
        file.close()

    # -------------------------- Locations --------------------------
    with locations_fp.open("r+", encoding="utf-8") as file:
        print(f"Generating: {locations_fp.resolve()}")
        existing_data = file.read() or "[]"
        existing_data = json.loads(existing_data)
        data = list(set(existing_data + locations))
        data = json.dumps(data, sort_keys=True, indent=4)
        file.seek(0)
        file.write(data)
        file.truncate()
        file.close()

    # -------------------------- Theater --------------------------
    with threatee_fp.open("r+", encoding="utf-8") as file:
        print(f"Generating: {threatee_fp.resolve()}")
        existing_data = file.read() or "[]"
        existing_data = json.loads(existing_data)
        data = list(set(existing_data + theater))
        data = json.dumps(data, sort_keys=True, indent=4)
        file.seek(0)
        file.write(data)
        file.truncate()
        file.close()

    # -------------------------- Reasons --------------------------
    with raisins_fp.open("r+", encoding="utf-8") as file:
        print(f"Generating: {raisins_fp.resolve()}")
        existing_data = file.read() or "[]"
        existing_data = json.loads(existing_data)
        data = list(set(existing_data + reasons))
        data = json.dumps(data, sort_keys=True, indent=4)
        file.seek(0)
        file.write(data)
        file.truncate()
        file.close()


if __name__ == "__main__":
    main()
