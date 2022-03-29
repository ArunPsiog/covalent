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

import os
from multiprocessing import Queue as MPQ
from typing import Any
from io import BytesIO
import requests
import cloudpickle as pickle
from refactor.dispatcher.app.schemas.workflow import (
    CancelWorkflowResponse,
    DispatchWorkflowResponse,
    Node,
    UpdateWorkflowResponse,
)
from dotenv import load_dotenv
from fastapi import APIRouter

from ....core.cancel_workflow import cancel_workflow_execution
from ....core.dispatch_workflow import dispatch_workflow
from ....core.update_workflow import update_workflow_results

load_dotenv()

BASE_URI = os.environ.get("DATA_OS_SVC_HOST_URI")
TOPIC = os.environ.get("MQ_DISPATCH_TOPIC")
MQ_CONNECTION_URI = os.environ.get("MQ_CONNECTION_URI")

tasks_queue = MPQ()
workflow_status_queue = MPQ()
router = APIRouter()

# Do we need this here?
mock_result = {
    "status": "COMPLETED",
    "result": {
        "dispatch_id": "",
        "results_dir": "",
        "status": "COMPLETED",
        "graph": {
            "links": [{"edge_name": "data", "param_type": "kwarg", "source": 0, "target": 1}],
            "nodes": [
                {
                    "name": "load_data",
                    "metadata": {"executor": "<LocalExecutor>"},
                    "function_string": "@ct.electron\ndef load_data():\n    iris = datasets.load_iris()\n    perm = permutation(iris.target.size)\n    iris.data = iris.data[perm]\n    iris.target = iris.target[perm]\n    return iris.data, iris.target\n\n\n",
                    "start_time": "2022-02-28T23:21:17.844268+00:00",
                    "end_time": "2022-02-28T23:21:17.853741+00:00",
                    "status": "COMPLETED",
                    "output": ["[[5.  3.4 1.5 0.2]]"],
                    "error": None,
                    "sublattice_result": None,
                    "stdout": "",
                    "stderr": "",
                    "id": 0,
                    "doc": None,
                    "kwargs": None,
                }
            ],
        },
    },
}

def get_result(dispatch_id: str):
    resp = requests.get(f"{BASE_URI}/api/v0/workflow/results/{dispatch_id}")
    return resp.content

@router.post("/{dispatch_id}", status_code=202, response_model=DispatchWorkflowResponse)
def submit_workflow(*, dispatch_id: str) -> Any:
    """
    Submit a workflow
    """
    result_pkl_bytes = get_result(dispatch_id)
    result = pickle.loads(result_pkl_bytes)
    result = dispatch_workflow(result, tasks_queue)
    result_pkl_bytes = pickle.dumps(result)
    result_file = BytesIO(result_pkl_bytes)
    requests.put(f"{BASE_URI}/api/v0/workflow/results/{dispatch_id}", files={'result_pkl_file': result_file})
    workflow_status_queue.put("RUNNING")  # Populate queue when workflow is running

    return {"response": f"{dispatch_id} workflow dispatched successfully"}


@router.delete("/{dispatch_id}", status_code=200, response_model=CancelWorkflowResponse)
def cancel_workflow(*, dispatch_id: str) -> CancelWorkflowResponse:
    """
    Cancel a workflow
    """

    resp = requests.get(f"{BASE_URI}/api/v0/workflow/results/{dispatch_id}")
    result_obj = resp.json()["result_obj"]

    success = cancel_workflow_execution(result_obj)

    if success:
        workflow_status_queue.get()  # Empty queue when workflow is terminated

        return {"response": f"{dispatch_id} workflow cancelled successfully"}
    else:
        return {"response": f"{dispatch_id} workflow did not cancel successfully"}


@router.put("/{dispatch_id}", status_code=200, response_model=UpdateWorkflowResponse)
def update_workflow(*, dispatch_id: str, task_execution_results: Node) -> UpdateWorkflowResponse:
    """
    Update a workflow
    """

    task_id = task_execution_results["task_id"]

    resp = requests.get(f"{BASE_URI}/api/v0/workflow/results/{dispatch_id}")
    result_obj = resp.json()["result_obj"]

    result_obj = update_workflow_results(task_execution_results, result_obj)

    if result_obj._status != "RUNNING":
        workflow_status_queue.get()  # Empty queue when workflow is no longer running (completed
        # or failed)

    requests.put(f"{BASE_URI}/api/v0/workflow/results/{dispatch_id}", data={result_obj})

    requests.put(f"{BASE_URI}/api/v0/ui/workflow/{dispatch_id}/task/{task_id}")

    return {"response": f"{dispatch_id} workflow updated successfully"}
