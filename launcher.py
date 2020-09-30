# Standard Library
import asyncio
import logging
import multiprocessing
import os
import pathlib
import signal
import sys
import time

from argparse import Namespace

# Cog Dependencies
import discord
import pkg_resources
import requests

# from bot import ClusterBot
from redbot.core import data_manager, drivers
from redbot.core._sharedlibdeprecation import SharedLibImportWarner
from redbot.core.bot import Red
from redbot.core.cli import confirm, interactive_config, parse_cli_flags

TOKEN = "NTk5MjE3NzIzNjU0MDEyOTg0.XraAJQ.7Cc5uFfJw1gcdaJ_Hm6MJpM0Uvc"

log = logging.getLogger("Cluster#Launcher")
log.setLevel(logging.DEBUG)
hdlr = logging.StreamHandler()
hdlr.setFormatter(logging.Formatter("[%(asctime)s %(name)s/%(levelname)s] %(message)s"))
fhdlr = logging.FileHandler("cluster-Launcher.log", encoding="utf-8")
fhdlr.setFormatter(logging.Formatter("[%(asctime)s %(name)s/%(levelname)s] %(message)s"))
log.handlers = [hdlr, fhdlr]


CLUSTER_NAMES = (
    "Alpha",
    "Beta",
    "Charlie",
    "Delta",
    "Echo",
    "Foxtrot",
    "Golf",
    "Hotel",
    "India",
    "Juliett",
    "Kilo",
    "Mike",
    "November",
    "Oscar",
    "Papa",
    "Quebec",
    "Romeo",
    "Sierra",
    "Tango",
    "Uniform",
    "Victor",
    "Whisky",
    "X-ray",
    "Yankee",
    "Zulu",
)
NAMES = iter(CLUSTER_NAMES)


def init_logging(level: int, location: pathlib.Path) -> None:
    dpy_logger = logging.getLogger("discord")
    dpy_logger.setLevel(logging.WARNING)
    base_logger = logging.getLogger("red")
    base_logger.setLevel(level)
    formatter = logging.Formatter("[%(asctime)s %(name)s/%(levelname)s] %(message)s")
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    base_logger.addHandler(stdout_handler)
    dpy_logger.addHandler(stdout_handler)


async def run_red_bot(log, red: Red, cli_flags: Namespace) -> None:
    """
    This runs the bot.

    Any shutdown which is a result of not being able to log in needs to raise
    a SystemExit exception.

    If the bot starts normally, the bot should be left to handle the exit case.
    It will raise SystemExit in a task, which will reach the event loop and
    interrupt running forever, then trigger our cleanup process, and does not
    need additional handling in this function.
    """
    driver_cls = drivers.get_driver_class()
    await driver_cls.initialize(**data_manager.storage_details())

    init_logging(level=cli_flags.logging_level, location=data_manager.core_data_path() / "logs")

    # log.debug("====Basic Config====")
    # log.debug("Data Path: %s", data_manager._base_data_path())
    # log.debug("Storage Type: %s", data_manager.storage_type())

    # lib folder has to be in sys.path before trying to load any 3rd-party cog (GH-3061)
    # We might want to change handling of requirements in Downloader at later date
    LIB_PATH = data_manager.cog_data_path(raw_name="Downloader") / "lib"
    LIB_PATH.mkdir(parents=True, exist_ok=True)
    if str(LIB_PATH) not in sys.path:
        sys.path.append(str(LIB_PATH))

        # "It's important to note that the global `working_set` object is initialized from
        # `sys.path` when `pkg_resources` is first imported, but is only updated if you do
        # all future `sys.path` manipulation via `pkg_resources` APIs. If you manually modify
        # `sys.path`, you must invoke the appropriate methods on the `working_set` instance
        # to keep it in sync."
        # Source: https://setuptools.readthedocs.io/en/latest/pkg_resources.html#workingset-objects
        pkg_resources.working_set.add_entry(str(LIB_PATH))
    sys.meta_path.insert(0, SharedLibImportWarner())

    if cli_flags.token:
        token = cli_flags.token
    else:
        token = os.environ.get("RED_TOKEN", None)
        if not token:
            token = await red._config.token()

    prefix = cli_flags.prefix or await red._config.prefix()

    if not (token and prefix):
        if cli_flags.no_prompt is False:
            new_token = await interactive_config(
                red, token_set=bool(token), prefix_set=bool(prefix)
            )
            if new_token:
                token = new_token
        else:
            log.critical("Token and prefix must be set in order to login.")
            sys.exit(1)

    if cli_flags.dry_run:
        await red.http.close()
        sys.exit(0)
    try:
        await red.start(token, bot=True, cli_flags=cli_flags)
    except discord.LoginFailure:
        log.critical("This token doesn't seem to be valid.")
        db_token = await red._config.token()
        if db_token and not cli_flags.no_prompt:
            if confirm("\nDo you want to reset the token?"):
                await red._config.token.set("")
                print("Token has been reset.")
                sys.exit(0)
        sys.exit(1)
    except Exception:
        log.exception("hmm")
        raise
    return None


def run_bot(log, autorestart: bool = False, shard_count: int = None, shard_ids: list = None):
    try:
        new_loop = asyncio.new_event_loop()
        cli_flags = parse_cli_flags(["qa", "--no-prompt", "--token", TOKEN])
        data_manager.load_basic_configuration(cli_flags.instance_name)
        red = Red(
            cli_flags=cli_flags,
            description="Red V3",
            dm_help=None,
            fetch_offline_members=True,
            loop=new_loop,
        )
        new_loop.run_until_complete(run_red_bot(log, red, cli_flags))
    except Exception as exc:
        log.exception(str(exc), exc_info=exc)


class Launcher:
    def __init__(self, loop):
        self.cluster_queue = []
        self.clusters = []

        self.fut = None
        self.loop = loop
        self.alive = True

        self.keep_alive = None
        self.init = time.perf_counter()

    def get_shard_count(self):
        data = requests.get(
            "https://discordapp.com/api/v7/gateway/bot",
            headers={
                "Authorization": "Bot " + TOKEN,
                "User-Agent": "DiscordBot (https://github.com/Rapptz/discord.py 1.3.0a) Python/3.7 aiohttp/3.6.1",
            },
        )
        data.raise_for_status()
        content = data.json()
        log.info(
            f"Successfully got shard count of {content['shards']} ({data.status_code, data.reason})"
        )
        return content["shards"]

    def start(self):
        self.fut = asyncio.ensure_future(self.startup(), loop=self.loop)

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.loop.run_until_complete(self.shutdown())
        finally:
            self.cleanup()

    def cleanup(self):
        self.loop.stop()
        if sys.platform == "win32":
            print("press ^C again")
        self.loop.close()

    def task_complete(self, task):
        if (exc := task.exception()) is not None:
            log.exception("err", exc_info=exc)
            task.print_stack()
            self.keep_alive = self.loop.create_task(self.rebooter())
            self.keep_alive.add_done_callback(self.task_complete)

    async def startup(self):
        shards = list(range(self.get_shard_count()))
        size = [shards[x : x + 4] for x in range(0, len(shards), 4)]
        log.info(f"Preparing {len(size)} clusters")
        for shard_ids in size:
            self.cluster_queue.append(Cluster(self, next(NAMES), shard_ids, len(shards)))

        await self.start_cluster()
        self.keep_alive = self.loop.create_task(self.rebooter())
        self.keep_alive.add_done_callback(self.task_complete)
        log.info(f"Startup completed in {time.perf_counter()-self.init}s")

    async def shutdown(self):
        log.info("Shutting down clusters")
        self.alive = False
        if self.keep_alive:
            self.keep_alive.cancel()
        for cluster in self.clusters:
            cluster.stop(sign=signal.CTRL_C_EVENT)
        self.cleanup()

    async def rebooter(self):
        while self.alive:
            # log.info("Cycle!")
            if not self.clusters:
                log.warning("All clusters appear to be dead")
                asyncio.ensure_future(self.shutdown())
            to_remove = []
            for cluster in self.clusters:
                if not cluster.process.is_alive():
                    if cluster.process.exitcode != 0:
                        # ignore safe exits
                        log.info(
                            f"Cluster#{cluster.name} exited with code {cluster.process.exitcode}"
                        )
                        log.info(f"Restarting cluster#{cluster.name}")
                        await cluster.start()
                    else:
                        log.info(f"Cluster#{cluster.name} found dead")
                        to_remove.append(cluster)
                        cluster.stop(sign=signal.CTRL_C_EVENT)  # ensure stopped
            for rem in to_remove:
                self.clusters.remove(rem)
            await asyncio.sleep(5)

    async def start_cluster(self):
        if self.cluster_queue:
            for cluster in self.cluster_queue:
                log.info(f"Starting Cluster#{cluster.name}")
                await cluster.start()
                log.info("Done!")
                self.clusters.append(cluster)
            log.info("All clusters launched")
        else:
            log.error("No clusters to launch")


class Cluster:
    def __init__(self, launcher, name, shard_ids, shard_count):
        self.launcher = launcher
        self.process = None
        # self.kwargs = dict(
        #     token=TOKEN,
        #     command_prefix="$$",
        #     shard_ids=shard_ids,
        #     shard_count=shard_count,
        #     cluster_name=name,
        # )
        self.shard_count = shard_count
        self.shard_ids = shard_ids
        self.name = name
        self.log = logging.getLogger(f"Cluster#{name}")
        self.log.setLevel(logging.DEBUG)
        hdlr = logging.StreamHandler()
        hdlr.setFormatter(logging.Formatter("[%(asctime)s %(name)s/%(levelname)s] %(message)s"))
        fhdlr = logging.FileHandler("cluster-Launcher.log", encoding="utf-8")
        fhdlr.setFormatter(logging.Formatter("[%(asctime)s %(name)s/%(levelname)s] %(message)s"))
        self.log.handlers = [hdlr, fhdlr]
        self.log.info(f"Initialized with shard ids {shard_ids}, total shards {shard_count}")

    def wait_close(self):
        return self.process.join()

    async def start(self, *, force=False):
        if self.process and self.process.is_alive():
            if not force:
                self.log.warning(
                    "Start called with already running cluster, pass `force=True` to override"
                )
                return
            self.log.info("Terminating existing process")
            self.process.terminate()
            self.process.close()
        stdout, stdin = multiprocessing.Pipe()
        # kw = self.kwargs
        # kw["pipe"] = stdin
        # self.process = multiprocessing.Process(
        #     target=run_bot(shard_ids=self.shard_ids), kwargs=kw, daemon=True
        # )
        self.process = multiprocessing.Process(
            name=self.name,
            target=run_bot,
            daemon=True,
            args=(self.log,),
            kwargs=dict(shard_count=self.shard_count, shard_ids=self.shard_ids),
        )
        self.process.start()
        self.log.info(f"Process started with PID {self.process.pid}")
        # if await self.launcher.loop.run_in_executor(None, stdout.recv) == 1:
        #     stdout.close()
        self.log.info("Process started successfully")
        return True

    def stop(self, sign=signal.SIGINT):
        self.log.info(f"Shutting down with signal {sign!r}")
        try:
            os.kill(self.process.pid, sign)
        except ProcessLookupError:
            pass


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    Launcher(loop).start()
