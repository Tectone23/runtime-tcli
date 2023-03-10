import importlib
import json
from os import walk, path, mkdir, getenv, chdir, getcwd
import platform
import re
from types import ModuleType
from urllib.error import URLError
from urllib.request import urlopen
from rich import print as pprint
from rich.progress import Progress, wrap_file
import yaml

from .api_service import Service, Templates
from .watch import Nelka, EventHandler

def print(*args, **kwargs):
    pprint(f"[bold green]Init -> {' '.join([str(_) for _ in args])} [/bold green]",**kwargs)

## *&*(-all object
class Resolve(object):
    def __setitem__(self, key, value):
        setattr(self, key, value)
    def __getitem__(self, key):
        return getattr(self, key)

    def __init__(self, **kwargs) -> None:
        for arg in kwargs:
            self[arg] = kwargs[arg]
        super().__init__()

class Data:
    def __init__(
        self,
        data
    ) -> None:
        self.data = data

    def toString(self):
        return "".join([_.decode("utf-8") for _ in self.data])

def fetch(
    location: str,
    title: str
) -> str:
    data: list = []
    try:
        response = urlopen(location)
        size = int(response.headers["Content-Length"])
        with wrap_file(response, size, description=f"[red]\[{title}]") as file:
            for line in file:
                data.append(line)
        return Data(data)
    except Exception as e:
        print(f"Failed to download resource \[{title}] at {location} due to {e}")


class Init:
    def __init__(
        self,
        cog_path: str,
        version: str,
        preprocessor: str,
        service: bool
    ) -> None:
        print("Preparing runtime environment")

        # Check directories
        self.check_directories()

        # Load config
        self.config = json.load(
            open(
                "./config/config.json",
                "r"
            )
        )

        self.cog_path = cog_path
        if not path.exists("./src/resources/runtime.py"):
            self.env: Resolve = self.resolve_version(version)
        self.preprocessor = preprocessor

        # Start watching
        watch = Nelka(
            event_handler= EventHandler(
                on_modified= self.set_routes
            ),
            track_only= [cog_path]
        )

        watch.start()

        if service:
            self.service = Service()

    def check_directories(self):
        EMULATED = path.join(getenv('HOME'), ".tcore_emulated")
        EMULATED_PATHS = [
            "safespace"
        ]

        if not path.exists(EMULATED):
            mkdir(EMULATED)
            for _path in EMULATED_PATHS:
                mkdir(path.join(EMULATED, _path))

    def safespace(self):
        chdir(path.join(getenv('HOME'), ".tcore_emulated", "safespace"))
        with open(".log", "w+") as f:
            from datetime import datetime
            now = datetime.now()
            time = now.strftime("%d/%m/%Y %H:%M:%S")
            f.write(f"safespace accessed at {time}")

    def resolve_version(
        self,
        version: str
    ) -> Resolve:
        """
        Finds the resource link for a runtime and preprocessor version
        """
        resources_url = self.config['resources']
        resources_file = fetch(resources_url, "Resources file").toString()
        runtime_resource = json.loads(resources_file)['runtime']

        runtime: Data = fetch(runtime_resource[version]['url'], "Runtime")


        resolve = Resolve(
            runtime = runtime.toString()
        )

        # Save runtime
        with open("src/resources/runtime.py", "w+") as f:
            f.write(runtime.toString())

        return resolve

    def fetch_version(
        self
    ):
        """
        Downloads latest release of the runtime
        """
        version_url = self.version.runtime
        data = []
        try:
            response = urlopen(version_url)
            size = int(response.headers["Content-Length"])
            with wrap_file(response, size, description=f"[red]\[Runtime-{self.version}]") as file:
                for line in file:
                    data.append(line)
        except Exception as e:
            print(f"Failed to download resource \[Runtime-{self.version}] at Runtime-{self.version}")

    def run_env(
        self
    ):
        import readline  # optional, will allow Up/Down/History in the console
        import code

        def scope():
            from resources.runtime import (
                System,
                logging
            )
            from resources.runtime import mainTextCode as executeCode
            variables = locals().copy()

            # Add functions to variables
            function_objects, cog_name = self.get_actions()
            variables.update({_.__name__: _ for _ in function_objects})

            shell = code.InteractiveConsole(variables)
            self.safespace()

            shell.interact(
                banner = f"""\
TCore Runtime 0.0.1 on Python {platform.python_version()}
This is an interactive runtime shell. Use with caution.
Use CTRL+D to exit""",
                exitmsg = """\
Farewell! Stopping runtime..."""
            )


        # Start scope session
        scope()

    def get_actions(self):
        # Load cog actions
        print(f"Loading actions from {self.cog_path}")

        try:
            root, dirs, files = next(walk(self.cog_path))
        except StopIteration:
            print(self.cog_path, getcwd())
            quit()

        c, h = False, False
        for file in files:
            if re.search(".*hooks", file):
                hooks = re.search(".*hooks", file).group(0)
                hooks_data = yaml.safe_load(open(path.join(self.cog_path, hooks), "r"))
                h = True
            if re.search(".*cog", file):
                cog = re.search(".*cog", file).group(0)
                cog_data = yaml.safe_load(open(path.join(self.cog_path, cog), "r"))
                c = True
        if not (c and h):
            raise Exception(
        f"{self.cog_path}, Cog Found: {c} Hooks Found: {h}"
        )

        # Located a valid cog entry,
        # start to load actions

        # Locate action entry
        try:
            cog_name = cog_data['name']
            actions = hooks_data['hook']['actions']
            source_path = hooks_data['hook']['source_path']
        except KeyError:
            raise Exception("Hooks file malformed, failed to load actions")

        function_objects: list[function] = []

        referenceHolder = Resolve()

        for action in actions:
            action_file = path.join(self.cog_path, source_path, actions[action]+".py")

            # Construct function object
            from resources import runtime
            
            function_object = runtime.build(
                action,
                open(action_file).read(),
                local = {"reference": referenceHolder}
            )
            
            function_object._code = open(action_file).read()
            function_objects.append(function_object)
            referenceHolder[function_object.__name__] = function_object
        
        return [function_objects, cog_name]

    def set_routes(self, _event = None):
        function_objects, cog_name = self.get_actions()
        final = Templates.FakeAsgard(cog_name, function_objects, self.safespace)
        self.service.generate_route(
            final
        )

    def run_session(
        self
    ):


        print("Generated asgard route 👍")

        self.set_routes()

        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self.service.serve()
        