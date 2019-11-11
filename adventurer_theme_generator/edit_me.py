# ----------------------------------------- Need manual input ----------------------------------------------------------
#  -------------- Theme Name ----------
from typing import List, Mapping, Tuple

__all__ = [
    "theme_name",
    "pet_count",
    "pet_names",
    "pet_modifiers",
    "item_count",
    "item_material",
    "item_modifier",
    "item_slots",
    "monster_count",
    "monster_names",
    "monster_attributes",
    "monster_modifiers",
    "any_monster_can_be_a_boss",
    "locations",
    "theater",
    "reasons",
]

theme_name: str = "Template"  # Name of the Theme

#  -------------- Pets values ----------
pet_count: int = 20000
# if the combination of all material, slots and modifiers dont reach this then you will have less items than this number

# Note: Add names in the order of how strong a pet should be, first is weakest, last is strongest
pet_names: List[str] = [
    "moth",
    "viper",
    "armadillo",
    "snake",
    "eel",
    "spider",
    "fox",
    "wolf",
    "cat",
    "boar",
    "owl",
    "imp",
    "leopard",
    "tiger",
    "eagle",
    "bear",
    "hippocampus",
    "ox",
    "leprechaun",
    "spirit",
    "hawk",
    "fairy",
    "wraith",
    "treant",
    "panther",
    "kirin",
    "griffin",
    "pegasus",
    "phoenix",
    "manticore",
    "chimera",
    "unicorn",
    "nymph",
    "dragon",
]
pet_modifiers: List[str] = [
    "majestic",
    "black",
    "blue",
    "rainbow",
    "angry",
    "sad",
    "annoyed",
    "large",
    "small",
    "demon",
    "snow",
    "giggling",
    "cave",
    "water",
    "fire",
    "wind",
    "earth",
    "frenzied",
    "red",
    "zephyr",
    "scruffy",
    "infernal",
    "forest",
    "desert",
    "swamp",
    "mountain",
]

#  -------------- Items values ----------
item_count: int = 20000  # Maximum number of items generated per rarity,
# if the combination of all material, slots and modifiers dont reach this then you will have less items than this number

# Note: Add names in the order of how strong a material/modifier should be, first is weakest, last is strongest
item_material: List[str] = [
    "leather",
    "hide",
    "fur",
    "raccoon fur",
    "wolf fur",
    "lion fur",
    "cloth",
    "silver",
    "gold",
    "diamond",
    "emerald",
    "iron",
    "wood",
    "silken",
    "tin",
    "chittin",
    "steel",
    "platinum",
    "bronze",
    "cooper",
    "glass",
    "obsidium",
    "dragonscale",
    "dragonplate",
    "unicorn horn",
    "orcish",
    "quicksilver",
    "ebony",
    "dwarven",
    "elven",
    "obsidium",
    "admantite",
    "aether",
    "colbalt",
    "dalekanium",
    "duranium",
    "etherium",
    "mithril",
    "nanite",
    "orichalcum",
    "redstone",
    "saronite",
    "unobtanium",
    "vibranium",
    "tachyon",
]
item_modifier: List[str] = [
    "old",
    "shiny",
    "polished",
    "small",
    "lucky",
    "moldy",
    "black",
    "short",
    "dented",
    "fine",
    "patched",
    "masterwork",
    "rusty",
    "plain",
    "carved",
    "sturdy",
    "broken",
    "dirty",
    "ancient",
    "godly",
    "heavenly",
    "thundering",
    "small",
    "large",
    "new",
    "golden",
    "hardened",
    "battle-worn",
    "demonized",
]

# Do not change the keys, only the list content
item_slots: Mapping[str, List[str]] = {
    "head": ["cap", "hat", "helmet"],
    "neck": ["collar", "necklace", "charm", "chain", "thread", "scarf"],
    "chest": ["cuirass", "overcoat", "jacket", "vest", "armor", "chainmail"],
    "gloves": ["gloves", "gauntlets"],
    "belt": ["belt", "rope", "armor", "chain"],
    "legs": ["chaps", "leggings", "guards", "pants", "skins", "legplates", "panis"],
    "boots": ["boots", "sandals", "sabatons", "shoes"],
    "left": [
        "sword",
        "club",
        "axe",
        "longsword",
        "dagger",
        "shield",
        "sling",
        "wand",
        "tome",
        "war axe",
        "rod",
    ],
    "right": ["sword", "club", "axe", "longsword", "dagger", "katana", "wand", "war axe"],
    "two handed": [
        "greatsword",
        "bow",
        "quarterstaff",
        "staff",
        "katana",
        "battle axe",
        "warhammer",
        "crossbow",
    ],
    "ring": ["ringlet", "amulet", "ring", "band"],
    "charm": ["figurine", "shard", "charm", "spellbook"],
}

#  -------------- Monsters values ----------
monster_count: int = 1000
# if the combination of names and modifiers don't reach this then you will have less items than this number
# Note: Add names in the order of how strong a modifier should be, first is weakest, last is strongest
monster_modifiers: List[str] = [
    "Red",
    "Blue",
    "Plagued",
    "Arcane",
    "Skeletal",
    "Earth",
    "Water",
    "Fire",
    "Wind",
    "Ice",
    "Ethereal",
    "Celestial",
]
# This one is a bit different ... we need the image url too, so its a list of Tuple
monster_names: List[Tuple[str, str]] = [
    ("Dove", "https://cdn.pixabay.com/photo/2016/02/23/20/31/dove-1218474_960_720.jpg"),
    ("Bat", "https://live.staticflickr.com/3741/9187712502_bbecd929e1_b.jpg"),
]

any_monster_can_be_a_boss: bool = False  # if True any mob has a 50/50 change of being a boss

# Name: [Health multiplier, diplomacy Multiplier]
monster_attributes: Mapping[str, List[float]] = {
    " terrifying": [1, 1.2],
    " staunch": [1.15, 1],
    " gigantic": [1.4, 1],
    " humongous": [2, 0.8],
    " prodigious": [1.6, 0.8],
    " hideous": [1, 1],
    " disgusting": [1, 0.7],
    " plagued": [1.2, 0.9],
    "n ordinary": [1, 1],
    " miniscule": [0.2, 1.1],
    " weary": [0.6, 0.9],
    " tiny": [0.7, 1],
    " small": [0.8, 1],
    " weak": [0.5, 1],
    " lazy": [0.4, 0.9],
    " sick": [0.3, 0.9],
    " stupid": [1, 0.5],
    " flustered": [0.9, 1.1],
    " delirious": [0.6, 0.8],
    " sad-looking": [0.9, 0.8],
    " cunning": [1.2, 1.2],
    " scheming": [1.3, 1],
    " highly-scarred": [1.4, 1.1],
    " focused": [1.2, 1],
    " fat": [1.1, 0.9],
    " muscle-bound": [1.2, 0.7],
    " fairly intelligent": [1, 1.2],
    " dumb": [1, 0.8],
    "n old": [0.8, 1.5],
    "n ancient": [0.8, 2],
    " savage": [1.8, 0.9],
    "n absolutely brutal-looking": [1.9, 1.1],
}

#  -------------- Location values ----------
locations: List[str] = [
    "There is telling of a dangerous cave nearby, holding immense riches. ",
    "There is a rumor of riches stored in a nearby cave. ",
    "You found a small clearing. ",
    "A bridge crosses over a deep gorge. ",
    "This town's inn looks very inviting. ",
    "A trail winds up the side of a mountain. ",
    "You hear a rumor of a treasure outside the town. ",
    "You found a clearing with sunshine streaming in from above. ",
    "The remains of some sort of ritual can be found ahead. ",
    "There is rumor of an adventurer's demise over the next hill. ",
    "A small path can be seen heading into some brush. ",
    "An overgrown grove lies ahead. ",
    "A deserted ritual space can be seen ahead. ",
    "The path widens and there is a small field. ",
    "You spy an ancient-looking chest resting against a tree. ",
    "The path ahead winds down into a valley below. ",
    "The birds and animals around you suddenly have gone silent. ",
    "There is a rumor that a rich dragon lives nearby. ",
    "You stumble upon a small grotto. ",
    "A thin, rickety wooden bridge stretches across a canyon. ",
    "You find a cave entrance covered in moss. ",
    "Thin tendrils of fog are starting to creep across the path. ",
    "There is a rumor of an ancient treasure nearby. ",
    "A small glittering object can be seen ahead on the side of the path. ",
    "The path opens up into a clearing, and fresh bones can be seen in the grass. ",
    "The path starts to thin and the trees feel like they are starting to reach towards you. ",
    "A mossy stone altar can be seen ahead. ",
    "A massive, short block of intricately-carved stone can be seen on the side of the path. ",
    "You hear a strange noise, unlike any animal you've heard before. ",
    "The birds suddenly stop singing and the silence in the forest is deafening. An open clearing lies ahead. ",
    "Rusty metal scraps are strewn about on the path ahead. ",
    "You stumble across the very fresh remains of another unfortunate adventurer. ",
]

#  -------------- Theater values ----------
theater: List[str] = [
    " menace",
    " glee",
    " malice",
    " all means necessary",
    " a couple of friends",
    " a crosseyed squint",
    " a steady pace",
    " a rumbling growl",
    " a lazy squint",
    " a hesitant step",
    " a tense glare",
    " an authoritative stance",
    " a cruel snarl",
    " agitated pacing",
    " an easy stride",
    " an animated pace",
    " terse growls",
    " defiance",
    " an indifferent squint",
    " contempt",
    " restless pacing",
    " a terrifying growl",
]

#  -------------- Reasons values ----------
reasons: List[str] = [
    " is going to investigate,",
    " is curious to have a peek,",
    " would like to have a look,",
    " wants to go there,",
    " thinks it would be a good idea to investigate,",
    " would like to go check it out,",
    " is excited to go see what could be found,",
    " thinks everyone should go check it out,",
    " is going to go take a look,",
    " thinks there could be treasure to be found,",
    " wants to go see,",
    " wants to investigate,",
    " is going to go sneak over to look,",
]
