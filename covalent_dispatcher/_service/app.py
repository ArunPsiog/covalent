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


"""Endpoints for dispatch management"""

import asyncio
import json
from contextlib import asynccontextmanager
from typing import List, Optional, Union
from uuid import UUID

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

import covalent_dispatcher.entry_point as dispatcher
from covalent._shared_files import logger
from covalent._shared_files.schemas.result import ResultSchema
from covalent._shared_files.util_classes import RESULT_STATUS
from covalent_dispatcher._core import dispatcher as core_dispatcher
from covalent_dispatcher._core import runner_ng as core_runner

from .._dal.exporters.result import export_result_manifest
from .._dal.result import Result, get_result_object
from .._db.datastore import workflow_db
from .._db.dispatchdb import DispatchDB
from .heartbeat import Heartbeat
from .models import ExportResponseSchema

app_log = logger.app_log
log_stack_info = logger.log_stack_info

router: APIRouter = APIRouter()

_background_tasks = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize global variables"""

    heartbeat = Heartbeat()
    fut = asyncio.create_task(heartbeat.start())
    _background_tasks.add(fut)
    fut.add_done_callback(_background_tasks.discard)

    # Runner event queue and listener
    core_runner._job_events = asyncio.Queue()
    core_runner._job_event_listener = asyncio.create_task(core_runner._listen_for_job_events())

    # Dispatcher event queue and listener
    core_dispatcher._global_status_queue = asyncio.Queue()
    core_dispatcher._global_event_listener = asyncio.create_task(
        core_dispatcher._node_event_listener()
    )

    yield

    # Cancel all scheduled and running dispatches
    for status in [
        RESULT_STATUS.NEW_OBJECT,
        RESULT_STATUS.RUNNING,
    ]:
        await cancel_all_with_status(status)

    core_dispatcher._global_event_listener.cancel()
    core_runner._job_event_listener.cancel()

    Heartbeat.stop()


async def cancel_all_with_status(status: RESULT_STATUS):
    """Cancel all dispatches with the specified status."""

    with workflow_db.session() as session:
        records = Result.get_db_records(
            session,
            keys=["dispatch_id"],
            equality_filters={"status": str(status)},
            membership_filters={},
        )
    for record in records:
        dispatch_id = record.attrs["dispatch_id"]
        await dispatcher.cancel_running_dispatch(dispatch_id)


@router.post("/dispatches/submit")
async def submit(request: Request) -> UUID:
    """
    Function to accept the submit request of
    new dispatch and return the dispatch id
    back to the client.

    Args:
        None

    Returns:
        dispatch_id: The dispatch id in a json format
                     returned as a Fast API Response object.
    """
    try:
        data = await request.json()
        data = json.dumps(data).encode("utf-8")
        return await dispatcher.make_dispatch(data)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to submit workflow: {e}",
        ) from e


@router.delete("/dispatches/{dispatch_id}/run")
async def cancel(dispatch_id: str, task_ids: List[int] = Query([])) -> str:
    """
    Function to accept the cancel request of
    a dispatch.

    Args:
        dispatch_id: ID of the dispatch
        task_ids: (Query) Optional list of specific task ids to cancel.
            An empty list will cause all tasks to be cancelled.

    Returns:
        Fast API Response object confirming that the dispatch
        has been cancelled.
    """

    await dispatcher.cancel_running_dispatch(dispatch_id, task_ids)
    print("DEBUG: task_ids", task_ids)
    if task_ids:
        return f"Cancelled tasks {task_ids} in dispatch {dispatch_id}."
    else:
        return f"Dispatch {dispatch_id} cancelled."


@router.get("/db-path")
def db_path() -> str:
    db_path = DispatchDB()._dbpath
    return json.dumps(db_path)


@router.post("/dispatches", status_code=201)
async def register(manifest: ResultSchema) -> ResultSchema:
    """Register a dispatch in the database.

    Args:
        manifest: Declares all metadata and assets in the workflow
        parent_dispatch_id: The parent dispatch id if registering a sublattice dispatch

    Returns:
        The manifest with `dispatch_id` and remote URIs for each asset populated.
    """
    try:
        return await dispatcher.register_dispatch(manifest, None)
    except Exception as e:
        app_log.debug(f"Exception in register: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to submit workflow: {e}",
        ) from e


@router.post("/dispatches/{dispatch_id}/subdispatches", status_code=201)
async def register_subdispatch(
    manifest: ResultSchema,
    dispatch_id: str,
) -> ResultSchema:
    """Register a subdispatch in the database.

    Args:
        manifest: Declares all metadata and assets in the workflow
        dispatch_id: The parent dispatch id

    Returns:
        The manifest with `dispatch_id` and remote URIs for each asset populated.
    """
    try:
        return await dispatcher.register_dispatch(manifest, dispatch_id)
    except Exception as e:
        app_log.debug(f"Exception in register: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to submit workflow: {e}",
        ) from e


@router.post("/dispatches/{dispatch_id}/redispatches", status_code=201)
async def register_redispatch(
    manifest: ResultSchema,
    dispatch_id: str,
    reuse_previous_results: bool = False,
):
    """Register a redispatch in the database.

    Args:
        manifest: Declares all metadata and assets in the workflow
        dispatch_id: The original dispatch's id.
        reuse_previous_results: Whether to try reusing the results of
            previously completed electrons.

    Returns:
        The manifest with `dispatch_id` and remote URIs for each asset populated.
    """
    try:
        return await dispatcher.register_redispatch(
            manifest,
            dispatch_id,
            reuse_previous_results,
        )
    except Exception as e:
        app_log.debug(f"Exception in register_redispatch: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to submit workflow: {e}",
        ) from e


@router.put("/dispatches/{dispatch_id}/run", status_code=202)
async def start(dispatch_id: str):
    """Start a previously registered (re-)dispatch.

    Args:
        `dispatch_id`: The dispatch's unique id.

    Returns:
        `dispatch_id`
    """
    fut = asyncio.create_task(dispatcher.start_dispatch(dispatch_id))
    _background_tasks.add(fut)
    fut.add_done_callback(_background_tasks.discard)

    return dispatch_id


@router.get("/dispatches/{dispatch_id}")
async def export_result(
    dispatch_id: str, wait: Optional[bool] = False, status_only: Optional[bool] = False
) -> ExportResponseSchema:
    """Export all metadata about a registered dispatch

    Args:
        `dispatch_id`: The dispatch's unique id.

    Returns:
        {
            id: `dispatch_id`,
            status: status,
            result_export: manifest for the result
        }

    The manifest `result_export` has the same schema as that which is
    submitted to `/register`.

    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        _export_result_sync,
        dispatch_id,
        wait,
        status_only,
    )


def _export_result_sync(
    dispatch_id: str, wait: Optional[bool] = False, status_only: Optional[bool] = False
) -> ExportResponseSchema:
    result_object = _try_get_result_object(dispatch_id)
    if not result_object:
        return JSONResponse(
            status_code=404,
            content={"message": f"The requested dispatch ID {dispatch_id} was not found."},
        )
    status = str(result_object.get_value("status", refresh=False))

    if not wait or status in [
        str(RESULT_STATUS.COMPLETED),
        str(RESULT_STATUS.FAILED),
        str(RESULT_STATUS.CANCELLED),
    ]:
        output = {
            "id": dispatch_id,
            "status": status,
        }
        if not status_only:
            output["result_export"] = export_result_manifest(dispatch_id)

        return output

    response = JSONResponse(
        status_code=503,
        content={"message": "Result not ready to read yet. Please wait for a couple of seconds."},
        headers={"Retry-After": "2"},
    )
    return response


def _try_get_result_object(dispatch_id: str) -> Union[Result, None]:
    try:
        res = get_result_object(
            dispatch_id, bare=True, keys=["id", "dispatch_id", "status"], lattice_keys=["id"]
        )
    except KeyError:
        res = None
    return res
