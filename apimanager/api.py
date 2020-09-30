from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING, Union

import aiohttp
import discord
import ujson

from .utils import User

if TYPE_CHECKING:
    from .main import APIManager

API_ENDPOINT = "https://api.redbot.app"


class API:
    _handshake_token: str = ""

    @classmethod
    async def get_all_users(cls, cog: APIManager) -> List[User]:
        async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
            async with session.get(
                f"{API_ENDPOINT}/api/v2/users/",
                headers=cog.headers,
                params={"limit": 1000},
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json(loads=ujson.loads)
                return [User(**u) for u in data]

    @classmethod
    async def get_user(
        cls, cog: APIManager, member: Union[discord.abc.User, discord.Object]
    ) -> Optional[User]:
        async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
            async with session.get(
                f"{API_ENDPOINT}/api/v2/users/user/{member.id}", headers=cog.headers
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json(loads=ujson.loads)
                return User(**data)

    @classmethod
    async def update_user(
        cls,
        cog: APIManager,
        member: Union[discord.abc.User, discord.Object],
        admin: bool = False,
        mod: bool = False,
        contrib: bool = False,
        user: bool = False,
        banned: bool = False,
        revoke_token: bool = False,
    ) -> Optional[User]:
        async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
            async with session.put(
                f"{API_ENDPOINT}/api/v2/users/user/{member.id}",
                headers=cog.headers,
                params={
                    "revoke_token": str(revoke_token).lower(),
                    "blacklist": str(banned).lower(),
                    "renew_token": "true",
                },
                json={
                    "is_admin": 1 if admin else 0,
                    "is_mod": 1 if mod else 0 ,
                    "is_contributor": 1 if contrib else 0,
                    "is_user": 1 if user else 0,
                    "is_guest": 0,
                },
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json(loads=ujson.loads)
                return User(**data)

    @classmethod
    async def create_user(cls, cog: APIManager, member: discord.Member) -> Optional[User]:
        async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
            async with session.post(
                f"{API_ENDPOINT}/api/v2/users/user",
                headers=cog.headers,
                params={
                    "user_id": str(member.id),
                    "name": str(member),
                    "is_user": 1,
                },
            ) as resp:
                if resp != 200:
                    return None
                data = await resp.json(loads=ujson.loads)
                return User(**data)

    @classmethod
    async def delete_user(
        cls, cog: APIManager, member: Union[discord.abc.User, discord.Object]
    ) -> Optional[User]:
        async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
            async with session.post(
                f"{API_ENDPOINT}/api/v2/users/user",
                headers=cog.headers,
                params={"user_id": str(member.id)},
            ) as resp:
                if resp != 200:
                    return None
                data = await resp.json(loads=ujson.loads)
                return User(**data)

    @classmethod
    async def ban_user(
        cls,
        cog: APIManager,
        member: Union[discord.abc.User, discord.Object],
        user_name: Optional[str] = "Banned",
    ) -> Optional[User]:
        async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
            async with session.post(
                f"{API_ENDPOINT}/api/v2/users/ban/user/{member.id}",
                headers=cog.headers,
                params={
                    "name": str(member)
                    if isinstance(member, discord.abc.User)
                    else user_name or "Banned"
                },
            ) as resp:
                if resp != 200:
                    return None
                data = await resp.json(loads=ujson.loads)
                return User(**data)

    @classmethod
    async def mass_ban_user(
        cls,
        cog: APIManager,
        users: List[int],
        mod: User,
        user_name: Optional[str] = "Banned",
    ) -> List[User]:
        params = [("name", user_name or "Banned")]
        for user in users:
            if await cog.is_allowed_by_hierarchy(mod, user):
                params.append(("users", str(user)))
        async with aiohttp.ClientSession(json_serialize=ujson.dumps) as session:
            async with session.post(
                f"{API_ENDPOINT}/api/v2/users/ban/multi",
                headers=cog.headers,
                params=params,
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json(loads=ujson.loads)
                return [User(**u) for u in data]
