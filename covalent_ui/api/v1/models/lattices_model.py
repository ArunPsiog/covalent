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

"""Lattice request and response model"""

from datetime import datetime
from enum import Enum
from typing import List, Union

from pydantic import BaseModel, ConfigDict

from covalent_ui.api.v1.models.dispatch_model import DispatchModule
from covalent_ui.api.v1.utils.models_helper import CaseInsensitiveEnum


class SubLatticeSortBy(CaseInsensitiveEnum):
    """Values to filter data by"""

    RUNTIME = "runtime"
    TOTAL_ELECTRONS = "total_electrons"
    LATTICE_NAME = "lattice_name"


class SubLatticeDetailResponse(BaseModel):
    sub_lattices: Union[List[DispatchModule], None] = None


class LatticeDetailResponse(BaseModel):
    """Lattices details model"""

    dispatch_id: Union[str, None] = None
    status: Union[str, None] = None
    total_electrons: Union[int, None] = None
    total_electrons_completed: Union[int, None] = None
    started_at: Union[datetime, None] = None
    ended_at: Union[datetime, None] = None
    directory: Union[str, None] = None
    description: Union[str, None] = None
    runtime: Union[int, None] = None
    updated_at: Union[datetime, None] = None


class LatticeDetail(BaseModel):
    dispatch_id: str
    status: str
    directory: str
    error_filename: str
    results_filename: str
    docstring_filename: str
    start_time: datetime
    end_time: datetime
    total_electrons: int
    total_electrons_completed: int
    runtime: int
    updated_at: datetime

    # class Config:
    #     from_attributes = True
    model_config = ConfigDict(from_attributes=True)


class LatticeDetailsFile(BaseModel):
    dispatch_id: str
    status: str
    directory: str
    error_filename: str
    function_string_filename: str
    executor: str
    executor_data_filename: str
    workflow_executor: str
    workflow_executor_data_filename: str
    error_filename: str
    inputs_filename: str
    results_filename: str
    storage_type: str
    function_filename: str
    transport_graph_filename: str
    started_at: str
    ended_at: str
    total_electrons: str
    total_electrons_completed: str

    # class Config:
    #     from_attributes = True
    model_config = ConfigDict(from_attributes=True)


class LatticeFileResponse(BaseModel):
    """Lattices File Response Model"""

    data: Union[str, None] = None
    python_object: Union[str, None] = None


class LatticeFileInput(BaseModel):
    """Lattices File Response Model"""

    data: Union[str, None] = None
    python_object: Union[dict, None] = None


class LatticeExecutorResponse(BaseModel):
    """Lattices File Response Model"""

    executor_name: Union[str, None] = None
    executor_details: Union[dict, None] = None


class LatticeWorkflowExecutorResponse(BaseModel):
    """Lattices File Response Model"""

    workflow_executor_name: Union[str, None] = None
    workflow_executor_details: Union[dict, None] = None


class GraphNodes(BaseModel):
    id: int = None
    name: str = None
    node_id: int = None
    started_at: datetime = None
    completed_at: datetime = None
    status: str = None
    type: str = None
    executor: str = None

    # Immediate parent electron id
    parent_electron_id: Union[None, int] = None

    # Is_parent field introduced to for graph box
    is_parent: Union[None, int] = None

    # Immediate parent dispatch id, to get electrons details
    parent_dispatch_id: Union[None, str] = None

    # Allow users to copy dispatch id a sublattice
    sublattice_dispatch_id: Union[None, str] = None


class GraphResponseData(BaseModel):
    nodes: List[GraphNodes] = None
    links: List[dict] = None


class GraphResponse(BaseModel):
    """Graph Response Model"""


class LatticeFileOutput(str, Enum):
    """Lattices file names"""

    RESULT = "result"
    FUNCTION_STRING = "function_string"
    INPUTS = "inputs"
    ERROR = "error"
    EXECUTOR = "executor"
    WORKFLOW_EXECUTOR = "workflow_executor"
    FUNCTION = "function"
    TRANSPORT_GRAPH = "transport_graph"
