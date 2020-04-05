# -*- coding: utf-8 -*-
# Standard Library
from random import choice, getrandbits, randint, sample, shuffle, uniform


class PetMaker:
    def __init__(self, name, modifier, petname_list):
        self.name = name
        self.modifier = modifier
        self.make_name()
        index = petname_list.index(name)
        self.bonus = min(randint(101, randint(101, randint(101, 199))) + index, 199) / 100
        self.crit = max(
            randint(-randint(index * 1, index * 3), randint(index * 1, index * 3)), index
        )
        self.cha = int((index + self.crit + randint(index * 3, index * 8)) * self.bonus)

    def make_name(self):
        self.name = f"{self.modifier} {self.name}"

    def to_json(self) -> dict:
        output = {self.name: {"name": self.name, "bonus": self.bonus, "cha": self.cha}}

        return output

    @classmethod
    def gen_pets(cls, count, pet_names, pet_modifiers, existing_data=None):
        data = existing_data or {}
        breaker = 0
        while count > 0:
            item = PetMaker(choice(pet_names), choice(pet_modifiers), pet_names).to_json()
            if list(item.keys())[0] not in data:
                data.update(item)
                count -= 1
                breaker -= 1
            else:
                breaker += 1
                if breaker > count * 2:
                    break
        return data


class ItemMaker:
    def __init__(self, rarity, slot, slots_data, prop, material):
        self.rarity = rarity
        self.material = choice(material)
        self.status = choice(prop)
        self.name = choice(slots_data[slot])
        self._slot = slot
        self.slot = []
        self.update_slot()
        self.make_name()
        self.index_material = material.index(self.material)
        self.index_status = prop.index(self.status)
        self.int = 0
        self.cha = 0
        self.att = 0
        self.dex = 0
        self.luck = 0
        self.calculate_stats()

    def update_slot(self):
        self.slot = [self._slot] if self._slot != "two handed" else ["right", "left"]

    def make_name(self):
        self.name = f"{self.status} {self.material} {self.name}"
        if self.rarity == 1:
            self.name = self.name
        if self.rarity == 2:
            self.name = "." + self.name.replace(" ", "_")
        if self.rarity == 3:
            self.name = f"[{self.name}]"
        if self.rarity == 4:
            self.name = f"{{Legendary:'{self.name.title()}'}}"

    def calculate_stats(self):
        stats = ["att", "cha", "int", "dex", "luck"]

        if self.rarity == 1:
            mininum, maximum = 0, 4
        elif self.rarity == 2:
            mininum, maximum = 3, 8
        elif self.rarity == 3:
            mininum, maximum = 6, 12
        elif self.rarity == 4:
            mininum, maximum = 8, 18
        else:
            mininum, maximum = 0, 4

        totalstats = randint(mininum, maximum)
        stats = sample(stats, min(randint(1, 6), 5))
        len_stats = len(stats)
        count = len_stats
        stats_based_on_material = randint(self.index_material * 1, self.index_material * 2)
        stats_based_on_status = randint(self.index_status * 1, self.index_status * 2)
        stats_based_on_multiplier = (stats_based_on_material + stats_based_on_status) / (
            self.index_material + self.index_status or 1
        )
        while count > 0:
            shuffle(stats)
            count -= 1
        for stat in stats:
            val = int(totalstats * self.rarity / len_stats) + int(stats_based_on_multiplier)
            if val >= 0:
                value = min(randint(0, val), maximum)
            else:
                value = min(randint(val, 0), maximum)
            totalstats -= value
            len_stats -= 1
            setattr(self, stat, value)

    def to_json(self) -> dict:
        output = {self.name: {"slot": self.slot}}
        stats = ["att", "cha", "int", "dex", "luck"]
        for stat in stats:
            val = getattr(self, stat)
            if val > 0 or val < 0:
                output[self.name].update({stat: val})
        while len(output[self.name]) < 2:
            stat = choice(stats)
            if stat not in output[self.name]:
                output[self.name].update({stat: 0})

        return output

    @classmethod
    def gen_items(cls, rarity, count, slots_data, prop, material, existing_data=None):
        data = existing_data or {}
        breaker = 0
        while count > 0:
            item = ItemMaker(
                rarity, choice(list(slots_data.keys())), slots_data, prop, material
            ).to_json()
            if list(item.keys())[0] not in data:
                data.update(item)
                count -= 1
                breaker -= 1
            else:
                breaker += 1
                if breaker > count * 2:
                    break
        return data


class MonsterMaker:
    def __init__(self, name, modifier, monster_list, monster_modifiers, is_boss=False):
        tuple_item = name
        self.name = tuple_item[0]
        self.image_url = tuple_item[-1]
        self.modifier = modifier
        self.make_name()
        index = monster_list.index(name)
        index_modifier = monster_modifiers.index(modifier)
        self.is_boss = is_boss
        self.hp = int(
            10 // (uniform(0.5, 2) if not self.is_boss else uniform(0.3, 1)) * index_modifier
            + index // (len(monster_list) + len(monster_modifiers))
        )
        self.pdef = round(uniform(0.5, uniform(uniform(0.5, 2) + uniform(0, 0.5), 2.5)), 2)
        self.mdef = round(uniform(0.5, uniform(uniform(0.5, 2) + uniform(0, 0.5), 2.5)), 2)
        self.dipl = int(self.hp // (uniform(0.5, 2) if not self.is_boss else uniform(0.3, 1.5)))

    def make_name(self):
        self.name = f"{self.modifier} {self.name}"

    def to_json(self) -> dict:
        output = {
            self.name: {
                "hp": self.hp,
                "pdef": self.pdef,
                "mdef": self.mdef,
                "dipl": self.dipl,
                "boss": self.is_boss,
                "miniboss": {},
                "color": "",
                "image": self.image_url,
            }
        }

        return output

    @classmethod
    def gen_monsters(
        cls, count, monster_names, monster_modifiers, existing_data=None, any_can_be_boss=False
    ):
        data = existing_data or {}
        breaker = 0
        while count > 0:
            monster = MonsterMaker(
                choice(monster_names),
                choice(monster_modifiers),
                monster_names,
                monster_modifiers,
                is_boss=bool(getrandbits(1)) if any_can_be_boss else False,
            ).to_json()
            if list(monster.keys())[0] not in data:
                data.update(monster)
                count -= 1
                breaker -= 1
            else:
                breaker += 1
                if breaker > count * 2:
                    break
        return data
