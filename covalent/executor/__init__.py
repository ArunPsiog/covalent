# Copyright 2021 Agnostiq Inc.
#
# This file is part of Covalent.
#
# Licensed under the GNU Affero General Public License 3.0 (the "License").
# A copy of the License may be obtained with this software package or at
#
#      https://www.gnu.org/licenses/agpl-3.0.en.html
#
# Use of this file is prohibited except in compliance with the License. Any
# modifications or derivative works of this file must retain this copyright
# notice, and modified files must contain a notice indicating that they have
# been altered from the originals.
#
# Covalent is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the License for more details.
#
# Relief from the License may be granted by purchasing a commercial license.

"""
Defines executors and provides a "manager" to get all available executors
"""

import contextlib
import glob
import importlib
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Union

import pkg_resources

from .._shared_files import logger
from .._shared_files.config import get_config, update_config
from .base import BaseExecutor, wrapper_fn
from ..quantum import QCluster, Simulator

app_log = logger.app_log
log_stack_info = logger.log_stack_info

_QUANTUM_PLUGINS_PATH = Path(__file__).parent / "quantum_plugins"
_QUANTUM_DEFAULTS_VARNAME = "_QEXECUTOR_PLUGIN_DEFAULTS"

class _ExecutorManager:
    """
    Executor manager to return a valid executor which can be
    used as an argument to electron and lattice decorators.

    Initializing generates a list of available executor plugins.
    """

    def __init__(self) -> None:
        # Dictionary mapping executor name to executor class
        self.executor_plugins_map: Dict[str, Any] = {}
        self.executor_plugins_exports_map: Dict[str, Any] = {}

        if os.environ.get("COVALENT_PLUGIN_LOAD", "true").lower() == "true":
            self.generate_plugins_list()

    def __new__(cls):
        # Singleton pattern for this class
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
        return cls.instance

    def generate_plugins_list(self) -> None:
        """
        Generate a list of available executor plugins.
        This is called automatically when the class is initialized.

        The list of executors is generated by loading the already
        installed plugins and the plugins in the executor directory.

        These executor plugins are loaded by importing the module that
        contains the plugin.

        The module should have an attribute named executor_plugin_name
        which is set to the class name defining the plugin.

        Args:
            None

        Returns:
            None
        """

        # Load plugins that are part of the covalent path:
        pkg_plugins_path = os.path.join(os.path.dirname(__file__), "executor_plugins")
        self._load_executors(pkg_plugins_path)

        # Look for executor plugins in a user-defined path:
        user_plugins_path = ":".join(
            filter(
                None,
                [
                    get_config("sdk.executor_dir"),
                    os.environ.get("COVALENT_EXECUTOR_DIR"),
                ],
            )
        )
        self._load_executors(user_plugins_path)

        # Look for pip-installed plugins:
        self._load_installed_plugins()

    def get_executor(self, name: Union[str, BaseExecutor]) -> BaseExecutor:
        """
        Get an executor by name.
        This accepts a string like "local" or a BaseExecutor instance.

        Args:
            name: The name of the executor to get.

        Returns:
            executor: An executor object.

        Raises:
            ValueError: If name is not found and new is False.
            TypeError: If name is not a string or a BaseExecutor instance.
        """

        if isinstance(name, BaseExecutor):
            return name

        elif isinstance(name, str):
            if name in self.executor_plugins_map:
                update_config()
                default_options = get_config(f"executors.{name}")
                return self.executor_plugins_map[name](**default_options)
            else:
                message = f"No executor found by name: {name}."
                app_log.error(message)
                raise ValueError(f"No executor found by name: {name}")
        else:
            message = f"Input must be of type str or BaseExecutor, not {type(name)}"
            app_log.error(message)
            raise TypeError

    def _is_plugin_name_valid(self, the_module):
        """Assert if the plugin variable name is valid"""

        plugin_name_var = "EXECUTOR_PLUGIN_NAME"
        return bool(
            hasattr(the_module, plugin_name_var) or hasattr(the_module, plugin_name_var.lower())
        )

    def nonzero_plugin_classes(self, plugin_class):
        """Retrun true if any plugin classes are present"""

        return bool(len(plugin_class))

    def _populate_executor_map_from_module(self, the_module: Any) -> None:
        """
        Populate the executor map from a module.
        Also checks whether `EXECUTOR_PLUGIN_NAME` is defined in the module.

        Args:
            the_module: The module to populate the executor map from.

        Returns:
            None
        """

        if not self._is_plugin_name_valid(the_module):
            message = f"{the_module.__name__} does not seem to have a well-defined plugin class.\n"
            message += f"Specify the plugin class with 'EXECUTOR_PLUGIN_NAME = <plugin class name>' in the {the_module.__name__} module."
            app_log.warning(message)
            return

        # All classes loaded by the module
        all_classes = inspect.getmembers(the_module, inspect.isclass)
        # Classes that are defined in the module:
        module_classes = [c[1] for c in all_classes if c[1].__module__ == the_module.__name__]
        # The module should have a global attribute named EXECUTOR_PLUGIN_NAME
        # which is set to the class name defining the plugin.
        executor_name = (
            the_module.executor_plugin_name
            if hasattr(the_module, "executor_plugin_name")
            else the_module.EXECUTOR_PLUGIN_NAME
        )
        plugin_class = [c for c in module_classes if c.__name__ == executor_name]

        if self.nonzero_plugin_classes(plugin_class):
            plugin_class = plugin_class[0]
            short_name = the_module.__name__.split("/")[-1].split(".")[-1]
            self.executor_plugins_map[short_name] = plugin_class

            if hasattr(the_module, "_EXECUTOR_PLUGIN_DEFAULTS"):
                default_params = {
                    "executors": {short_name: getattr(the_module, "_EXECUTOR_PLUGIN_DEFAULTS")},
                }
                update_config(default_params, override_existing=False)

        else:
            # The requested plugin (the_module.module_name) was not found in the module.
            executor_name = (
                the_module.executor_plugin_name
                if hasattr(the_module, "executor_plugin_name")
                else the_module.EXECUTOR_PLUGIN_NAME
            )
            message = (
                f"Requested executor plugin {executor_name} was not found in {the_module.__name__}"
            )
            app_log.warning(message)

    def _load_installed_plugins(self) -> None:
        """
        Load executor plugins from pip.
        Populates the executor_plugins_map attribute.

        Args:
            None

        Returns:
            None
        """

        entry_points = pkg_resources.iter_entry_points("covalent.executor.executor_plugins")
        for entry in entry_points:
            the_module = entry.load()
            self._populate_executor_map_from_module(the_module)

    def _load_executors(self, executor_dir: str) -> None:
        """
        Load executor plugins from a directory.
        Populates the executor map and executor_plugins_map attributes with user's plugins.

        Args:
            executor_dir: The directory to load executor plugins from.

        Returns:
            None
        """

        dirs = set(executor_dir.split(":"))

        for e_dir in dirs:
            if os.path.exists(e_dir):
                module_files = glob.glob(os.path.join(e_dir, "*.py"))

                for module_file in module_files:
                    if module_file.endswith("__init__.py"):
                        continue

                    module_name = module_file[:-3]

                    # Import the module that contains the plugin
                    module_spec = importlib.util.spec_from_file_location(module_name, module_file)
                    the_module = importlib.util.module_from_spec(module_spec)
                    module_spec.loader.exec_module(the_module)

                    self._populate_executor_map_from_module(the_module)

    def list_executors(self, regenerate: bool = False, print_names: bool = True) -> List[str]:
        """
        Return and optionally print the executors that are available.

        Args:
            regenerate: If True, the executor map is regenerated.
            print_names: If True, executor names are printed as well.

        Returns:
            A list of executor names.
        """

        if regenerate:
            self.generate_plugins_list()

        executor_list = []
        for n, name in enumerate(self.executor_plugins_map, start=1):
            executor_list.append(name)
            if print_names:
                print(f"{n}. {name}")

        return executor_list


class _QExecutorManager:
    """
    QExecutor manager to return a valid QExecutor which can be
    used as an argument to `qelectron` decorator.

    Initializing generates a list of available QExecutor plugins.
    """

    def __init__(self):
        # Dictionary mapping executor name to executor class
        self.executor_plugins_map: Dict[str, Any] = {
            "QCluster": QCluster,
            "Simulator": Simulator,
        }
        self.load_executors()

    def __new__(cls):
        # Singleton pattern for this class
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_executors(self) -> None:
        """
        Looks for `plugin.py` modules in the subdirectories of the given path and
        loads QExecutor classes from them.
        """

        # Iterate over all subdirectories of the plugins path except for those starting with "_" like "__pycache__"
        for plugin_dir in filter(lambda _p: _p.is_dir() and not _p.name.startswith("_"), _QUANTUM_PLUGINS_PATH.iterdir()):

            # Get the Path of the plugin module
            plugin_module_path = list(plugin_dir.glob("*_plugin.py"))
            if not plugin_module_path:
                continue
            plugin_module_path = plugin_module_path[0]

            if plugin_module_path.exists():
                print(f"PLUGIN MODULE STEM: {plugin_module_path.stem}")
                print(f"PLUGIN MODULE PATH: {plugin_module_path}")

                with contextlib.suppress(RuntimeError):
                    plugin_module_spec = importlib.util.spec_from_file_location(
                        plugin_module_path.stem,
                        plugin_module_path
                    )
                    plugin_module = importlib.util.module_from_spec(plugin_module_spec)
                    sys.modules[plugin_module_path.stem] = plugin_module
                    plugin_module_spec.loader.exec_module(plugin_module)
                    self.populate_executors_map(plugin_module)

    def populate_executors_map(self, module_obj) -> None:
        """
        Validates modules containing potential QExecutor classes.
        Populates the `executor_plugins_map` dictionary and updates the config.
        """

        self.validate_module(module_obj)

        for qexecutor_cls_name in getattr(module_obj, "__all__"):
            self.executor_plugins_map[qexecutor_cls_name] = getattr(module_obj, qexecutor_cls_name)

        for qexecutor_cls_name, defaults_dict in getattr(module_obj, _QUANTUM_DEFAULTS_VARNAME).items():
            update_config(
                {"qelectron": {qexecutor_cls_name: defaults_dict}},
                override_existing=False
            )

    def validate_module(self, module_obj) -> None:
        """
        Checks all of the following:
            - module exports plugin classes using `__all__`
            - module defines `_QUANTUM_DEFAULTS_VARNAME`
            - exported plugin classes match the default parameters

        """
        if not hasattr(module_obj, "__all__"):
            return
        if not hasattr(module_obj, _QUANTUM_DEFAULTS_VARNAME):
            return

        plugin_defaults = getattr(module_obj, _QUANTUM_DEFAULTS_VARNAME)

        if set(module_obj.__all__).difference(set(plugin_defaults)):
            raise RuntimeError(
                f"Module missing default parameters in {module_obj.__file__}"
            )
        if set(plugin_defaults).difference(set(module_obj.__all__)):
            raise RuntimeError(
                f"Non-exported QExecutor class in default parameters in {module_obj.__file__}"
            )


_executor_manager = _ExecutorManager()
_qexecutor_manager = _QExecutorManager()

for name in _executor_manager.executor_plugins_map:
    plugin_class = _executor_manager.executor_plugins_map[name]
    globals()[plugin_class.__name__] = plugin_class

for qexecutor_cls in _qexecutor_manager.executor_plugins_map.values():
    globals()[qexecutor_cls.__name__] = qexecutor_cls
