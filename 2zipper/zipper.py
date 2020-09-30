# -*- coding: utf-8 -*-
# Standard Library
import contextlib
import inspect
import tarfile

from pathlib import Path
from typing import Optional

# Cog Dependencies
import discord

from redbot.core import commands
from redbot.core.data_manager import cog_data_path

_ = lambda s: s


class Zipper(commands.Cog):
    """Drapers Dev commands."""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def _can_send(ctx, file_size) -> bool:
        if ctx.guild:
            max_size = ctx.guild.filesize_limit - 1000
        else:
            max_size = 8388608 - 1000
        return file_size <= max_size

    @staticmethod
    async def zip_folder(path: Path, new_file: Path) -> Path:
        to_zip = []
        exclusions = [
            "__pycache__",
            ".db",
            ".pyc",
            "Lavalink.jar",
            "cache.db",
            "Audio.db",
            "localtracks",
            "locales",
            ".po",
        ]
        for f in path.glob("**/*"):
            if not any(ex in str(f) for ex in exclusions) and f.is_file():
                to_zip.append(f)
        with tarfile.open(new_file, "w:gz") as tar:
            for f in to_zip:
                tar.add(str(f), arcname=f.relative_to(path), recursive=False)
        return new_file

    @staticmethod
    async def zip_file(path: Path, new_file: Path) -> Path:
        with tarfile.open(new_file, "w:gz") as tar:
            tar.add(str(path), arcname=new_file.relative_to(path), recursive=False)
        return new_file

    async def _zip_file(self, path) -> Path:
        zip_name = path.with_suffix(".tar.gz")
        zip_name = Path.home() / zip_name.name
        return await self.zip_file(path, new_file=zip_name)

    async def _zip_dir(self, path) -> Path:
        zip_name = Path.home() / "cog_zipped.tar.gz"
        await self.zip_folder(path, new_file=zip_name)
        return zip_name

    async def _pull_file(self, ctx, cog_name, filename) -> None:
        cog_obj = ctx.bot.get_cog(cog_name)
        if cog_obj is None:
            return await ctx.send(_("Unable to find a cog called: {cog}").format(cog=cog_name))
        path_to_cog = Path(inspect.getfile(type(cog_obj)))

        if filename:
            path_to_file = path_to_cog.parent / f"{filename}"
        else:
            path_to_file = path_to_cog

        try:
            if not (path_to_file.exists() and path_to_file.is_file()):
                return await ctx.send("I can't find that file.")
        except OSError:
            return await ctx.send("I can't find that file.")

        if await self._can_send(ctx, path_to_file.lstat().st_size):
            await ctx.send(file=discord.File(str(path_to_file)))
        else:
            await ctx.send("Zip file is too large to send via discord")
        return

    @commands.command()
    @commands.is_owner()
    async def postcog(self, ctx, cog_name: str, py_name: Optional[str] = None):
        """Send a cog or supporting py file to the current channel.

        Checks cog locations in this order: downloader-installed, core, custom cog paths
        """
        return await self._pull_file(ctx, cog_name, py_name)

    @commands.command()
    @commands.is_owner()
    async def postsettings(self, ctx, cog_name: str, file_name: Optional[str] = None):
        """Send the specified file or setting from the Cog data path to the current channel."""
        cog_obj = ctx.bot.get_cog(cog_name)
        if cog_obj is None:
            return await ctx.send(_("Unable to find a cog called: {cog}").format(cog=cog_name))
        data_path = cog_data_path(cog_instance=cog_obj)
        settings = data_path / ("settings.json" if file_name is None else file_name)

        try:
            if not (settings.exists() and settings.is_file()):
                return await ctx.send(
                    f"I can't find the {file_name if file_name else 'settings.json file'} for that cog."
                )
        except OSError:
            return await ctx.send(
                f"I can't find the {file_name if file_name else 'settings.json file'} for that cog."
            )

        if await self._can_send(ctx, settings.lstat().st_size):
            return await ctx.send(file=discord.File(str(settings)))

        new_zip = await self._zip_file(settings)
        if await self._can_send(ctx, new_zip.lstat().st_size):
            await ctx.send(file=discord.File(str(new_zip)))
        else:
            await ctx.send("Zip file is too large to send via discord")

        with contextlib.suppress(BaseException):
            new_zip.unlink()

    @commands.command()
    @commands.is_owner()
    async def postcogzip(self, ctx, cog_name: str):
        """Send a zip of the cog.

        Checks cog locations in this order: downloader-installed, core, custom cog paths
        """
        cog_obj = ctx.bot.get_cog(cog_name)
        if cog_obj is None:
            return await ctx.send(_("Unable to find a cog called: {cog}").format(cog=cog_name))
        path_to_cog = Path(inspect.getfile(type(cog_obj))).parent
        try:
            if not (path_to_cog.exists() and path_to_cog.is_dir()):
                return await ctx.send("I can't find that cog.")
        except OSError:
            return await ctx.send("I can't find that cog.")
        zio_file = await self._zip_dir(path_to_cog)
        if await self._can_send(ctx, zio_file.lstat().st_size):
            await ctx.send(file=discord.File(str(zio_file)))
        else:
            await ctx.send("Zip file is too large to send via discord")
        with contextlib.suppress(BaseException):
            zio_file.unlink()
