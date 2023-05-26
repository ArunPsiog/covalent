import asyncio
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import orjson
import pennylane as qml
from mpire import WorkerPool
from pydantic import BaseModel, Extra, Field, root_validator

__all__ = [
    "BaseQExecutor",
    "BaseProcessPoolQExecutor",
    "AsyncBaseQExecutor",
    "BaseThreadPoolQExecutor",
    "AsyncBaseQCluster"
]


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


@lru_cache
def get_process_pool(n_jobs=None):
    return WorkerPool(n_jobs=n_jobs)


@lru_cache
def get_thread_pool(max_workers=None):
    return ThreadPoolExecutor(max_workers=max_workers)


@lru_cache
def get_asyncio_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


class BaseQExecutor(ABC, BaseModel):

    persist_data: bool = True

    class Config:
        extra = Extra.allow

    @root_validator(pre=True)
    def set_name(cls, values):
        # Set the `name` attribute to the class name
        values["name"] = cls.__name__
        return values

    @abstractmethod
    def batch_submit(self, qscripts_list):
        raise NotImplementedError

    @abstractmethod
    def batch_get_result_and_time(self, futures_list):
        raise NotImplementedError

    def run_circuit(self, qscript, device, result_obj: 'QCResult') -> 'QCResult':
        start_time = time.perf_counter()
        results = qml.execute([qscript], device, None)
        end_time = time.perf_counter()

        result_obj.results = results
        result_obj.execution_time = end_time - start_time

        return result_obj


class QCResult(BaseModel):
    """
    Container for results from `run_circuit` methods. Standardizes output and allows
    metadata to be updated at various points.
    """

    results: Optional[Any] = None
    execution_time: float = None
    metadata: Dict[str, Any] = Field(default_factory=lambda: {"execution_metadata": []})

    @classmethod
    def with_metadata(cls, *, device_name: str, executor: BaseQExecutor):
        """
        create an blank instance with pre-set metadata
        """
        result_obj = cls()
        backend_name = ""
        if hasattr(executor, "backend_name"):
            backend_name = executor.backend_name

        result_obj.metadata.update(
            device_name=device_name,
            executor_name=executor.__class__.__name__,
            executor_backend_name=backend_name,
        )
        return result_obj


class SyncBaseQExecutor(BaseQExecutor):

    device: str = "default.qubit"

    def run_all_circuits(self, qscripts_list) -> List[QCResult]:

        result_objs: List[QCResult] = []

        for qscript in qscripts_list:
            dev = qml.device(self.device, wires=qscript.wires)

            result_obj = QCResult.with_metadata(
                device_name=dev.short_name,
                executor=self
            )
            result_obj = self.run_circuit(qscript, dev, result_obj)
            result_objs.append(result_obj)

        return result_objs

    def batch_submit(self, qscripts_list):
        # Offload execution of all circuits to the same thread
        # so that the qserver isn't blocked by their completion.
        pool = get_thread_pool()
        fut = pool.submit(self.run_all_circuits, qscripts_list)
        dummy_futures = [fut] * len(qscripts_list)
        return dummy_futures

    def batch_get_result_and_time(self, futures_list):
        return futures_list[0].result()


class AsyncBaseQExecutor(BaseQExecutor):
    """
    Executor that uses `asyncio` to handle multiple job submissions
    """

    # pylint: disable=invalid-overridden-method

    device: str = "default.qubit"

    def batch_submit(self, qscripts_list):

        futures = []
        loop = get_asyncio_event_loop()
        for qscript in qscripts_list:
            dev = qml.device(self.device, wires=qscript.wires)

            result_obj = QCResult.with_metadata(
                device_name=dev.short_name,
                executor=self,
            )
            fut = loop.create_task(self.run_circuit(qscript, dev, result_obj))
            futures.append(fut)

        return futures

    def batch_get_result_and_time(self, futures_list: List):

        loop = get_asyncio_event_loop()
        return loop.run_until_complete(
            self._get_result_and_time(futures_list)
        )

    async def _get_result_and_time(self, futures_list: List) -> List[QCResult]:
        return [await fut for fut in futures_list]

    async def run_circuit(self, qscript, device, result_obj) -> QCResult:
        await asyncio.sleep(0)
        start_time = time.perf_counter()
        results = qml.execute([qscript], device, None)
        end_time = time.perf_counter()

        result_obj.results = results
        result_obj.execution_time = end_time - start_time

        return result_obj


class BaseProcessPoolQExecutor(BaseQExecutor):

    device: str = "default.qubit"
    n_jobs: int = None

    def batch_submit(self, qscripts_list):
        pool = get_process_pool(self.n_jobs)

        futures = []
        for qscript in qscripts_list:
            dev = qml.device(self.device, wires=qscript.wires)

            result_obj = QCResult.with_metadata(
                device_name=dev.short_name,
                executor=self,
            )
            fut = pool.apply_async(self.run_circuit, args=(qscript, dev, result_obj))
            futures.append(fut)

        return futures

    def batch_get_result_and_time(self, futures_list: List) -> List[QCResult]:
        return [fut.get() for fut in futures_list]


class BaseThreadPoolQExecutor(BaseQExecutor):

    device: str = "default.qubit"
    max_workers: int = None

    def batch_submit(self, qscripts_list):
        pool = get_thread_pool(self.max_workers)

        futures = []
        for qscript in qscripts_list:
            dev = qml.device(self.device, wires=qscript.wires)

            result_obj = QCResult.with_metadata(
                device_name=dev.short_name,
                executor=self,
            )
            fut = pool.submit(self.run_circuit, qscript, dev, result_obj)
            futures.append(fut)

        return futures

    def batch_get_result_and_time(self, futures_list: List) -> List[QCResult]:
        return [fut.result() for fut in futures_list]


class AsyncBaseQCluster(AsyncBaseQExecutor):

    executors: Tuple[BaseQExecutor, ...]
    selector: Union[str, Callable]

    @abstractmethod
    def serialize_selector(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def deserialize_selector(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def dict(self, *args, **kwargs) -> dict:
        raise NotImplementedError
