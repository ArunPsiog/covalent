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
# Relief from the License may be granted by purchasing a commercial license.

"""Settings Route"""


from enum import Enum
from typing import Dict

from fastapi import APIRouter, HTTPException, status

from covalent._shared_files.config import CMType, get_config, update_config
from covalent_ui.api.v1.models.settings_model import (
    GetSettingsResponseModel,
    UpdateSettingsResponseModel,
    Validators,
)

routes: APIRouter = APIRouter()


class ConfigFileType(Enum):
    CLIENT = "client"
    SERVER = "server"


@routes.get("/settings", response_model=GetSettingsResponseModel)
def get_settings():
    """
    Read the configuration from file.

    Args:
        None

    Returns:
        Configuration file as json object.
    """
    return GetSettingsResponseModel(
        client=get_config(CMType.CLIENT), server=get_config(CMType.SERVER)
    )


@routes.post("/settings", response_model=UpdateSettingsResponseModel)
def post_settings(new_entries: Dict, override_existing: bool = True):
    """
    Update the exising configuration dictionary with the configuration sent in request body with
    respect to the type of configuration ex client/server.
    Only executor fields are writable.

    Args:
        new_entries: Dictionary of new entries added or updated in the config.
        override_existing: If True (default), config values from the config file
            or the input dictionary (new_entries) take precedence over any existing
            values in the config.

    Returns:
        settings updated successfully when updated.
    """

    if new_entries == {}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "loc": ["path", "update-settings"],
                    "msg": "Key should not be empty",
                    "type": None,
                }
            ],
        )
    file_type = next(iter(new_entries.keys()))
    first_key = next(iter(new_entries[file_type].keys()))
    if first_key == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "loc": ["path", "update-settings"],
                    "msg": "Key should not be empty string",
                    "type": None,
                }
            ],
        )
    if len([validator.value for validator in Validators if validator.value in new_entries]) != 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[
                {
                    "loc": ["path", "update-settings"],
                    "msg": "Field cannot be updated",
                    "type": None,
                }
            ],
        )
    if file_type == ConfigFileType.SERVER.value:
        update_config(CMType.SERVER, new_entries[file_type], override_existing)
        return UpdateSettingsResponseModel(data="server settings updated successfully")
    elif file_type == ConfigFileType.CLIENT.value:
        update_config(CMType.CLIENT, new_entries[file_type], override_existing)
        return UpdateSettingsResponseModel(data="client settings updated successfully")
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=[
            {
                "loc": ["path", "update-settings"],
                "msg": "invalid update request",
                "type": None,
            }
        ],
    )
