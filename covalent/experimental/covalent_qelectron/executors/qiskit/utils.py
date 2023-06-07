"""
Utilities for Qiskit-based QElectron executors and devices
"""
from dataclasses import dataclass
from typing import Optional

from qiskit_ibm_runtime import Options, options


@dataclass(frozen=True)
class RuntimeOptions:
    # pylint: disable=too-many-instance-attributes
    """
    Execution options of Qiskit Runtime
    """
    optimization_level: int = 3
    resilience_level: int = 1
    max_execution_time: Optional[int] = None
    transpilation: Optional[options.TranspilationOptions] = None
    resilience: Optional[options.ResilienceOptions] = None
    execution: Optional[options.ExecutionOptions] = None
    environment: Optional[options.EnvironmentOptions] = None
    simulator: Optional[options.SimulatorOptions] = None

    def get(self, k, default=None):
        """
        mimics a `dict` object's `get` method using instance's `__dict__`,
        defaults when the value is None
        """
        if k in self.__dict__ and self.__dict__[k]:
            return self.__dict__[k]
        return default


def extract_options(opts: dict) -> Options:
    """
    Construct a Qiskit `Options` object from the options dictionary
    """
    _options = Options()
    _options.optimization_level = opts.get("optimization_level", 3)
    _options.resilience_level = opts.get("resilience_level", 1)
    _options.max_execution_time = opts.get("max_execution_time", None)
    _options.transpilation = opts.get("transpilation", _options.transpilation)
    _options.resilience = opts.get("resilience", _options.resilience)
    _options.execution = opts.get("execution", _options.execution)
    _options.environment = opts.get("environment", _options.environment)
    _options.simulator = opts.get("simulator", _options.simulator)
    return _options
