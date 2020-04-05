import asyncio
import logging
from typing import Any, List, MutableMapping, Optional, Sequence, Tuple

import aiohttp
from redbot.core.bot import Red

from redbot.core import commands
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.chat_formatting import box, pagify
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .utils import NameGenerator

log = logging.getLogger("red.drapercogs.PokeGram")


class PokeGram(commands.Cog):
    """Pokegram commands."""

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.valid_names: Sequence[str] = []
        self.cog_ready_event: Optional[asyncio.Event] = None
        self.session: Optional[aiohttp.ClientSession] = None

    def cog_unload(self) -> None:
        if self.session:
            self.session.close()

    async def initialize(self) -> None:
        await self.bot.wait_until_red_ready()
        if not self.cog_ready_event:
            self.cog_ready_event = asyncio.Event()
        if not self.session:
            self.session = aiohttp.ClientSession()
        await self.fetch_names()
        self.cog_ready_event.set()

    async def cog_before_invoke(self, ctx: commands.Context) -> None:
        await self.cog_ready_event.wait()

    async def make_get(
        self, url: str, headers: MutableMapping = None, params: MutableMapping = None
    ) -> MutableMapping[str, Any]:
        """Make a GET request to the PokeAPI"""
        if params is None:
            params = {}
        async with self.session.request("GET", url, params=params, headers=headers) as r:
            data = await r.json()
            if r.status != 200:
                log.debug(f"Issue making GET request to {url}: [{r.status}] {data}")
                data = {}
            return data

    async def get_from_file(self) -> List[str]:
        namelist = bundled_data_path(self) / "nameslist.txt"
        with open(str(namelist), mode="r") as namelist_data:
            return [n.strip() for n in list(namelist_data) if n]

    async def fetch_names(self, api: bool = False) -> List[str]:
        name_list = []
        if api:
            data = await self.make_get(url="https://pokeapi.co/api/v2/pokemon/?offset=0&limit=807")
            for pokemon in data.get("results", []):
                name_list.append(pokemon["name"])
        else:
            name_list = await self.get_from_file()
        if name_list:
            self.valid_names = name_list
        return name_list

    async def find_anagrams(self, name: str) -> Tuple[List[str], str]:
        results = []
        remaining = ""
        if not self.valid_names:
            return results, remaining
        async for pokemon in NameGenerator(self.valid_names):
            new_name = ""
            split_name = list(name.lower())
            pkm_name_length = len(pokemon)
            for poke_letter in pokemon:
                if poke_letter in split_name:
                    new_name += poke_letter
                    split_name.remove(poke_letter)
            new_name += " "
            if new_name[:pkm_name_length] == pokemon:
                remaining = "".join(split_name)
                more_names, remaining = await self.find_anagrams(remaining)
                if not more_names:
                    results.append(new_name + remaining)
                else:
                    for item in more_names:
                        results.append(new_name + item)
            else:
                remaining = name
        return results, remaining

    @commands.command()
    @commands.is_owner()
    async def updatenames(self, ctx: commands.Context):
        """Fetch PokeAPI for up to date names."""
        await self.fetch_names()
        await ctx.tick()

    @commands.command()
    async def getanagram(self, ctx: commands.Context, *, poke_name: str):
        """Get the Anagram of a Pokemon."""
        assert isinstance(poke_name, str)
        results, remaining = await self.find_anagrams(poke_name)

        output = ""
        for index, name in enumerate(results, start=1):
            output += f"{index}. [{name}]\n"

        output = output.strip()
        pages = [box(page, lang="ini") for page in pagify(output, shorten_by=20, page_length=200)]
        if not pages:
            return await ctx.send("No anagram found for {name}.".format(name=poke_name))
        await menu(ctx, pages, DEFAULT_CONTROLS)
