#
# MIT License
#
# Copyright (c) 2020 Airbyte
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#


import base64
from typing import Any, List, Mapping, Tuple

import pendulum
from airbyte_cdk.logger import AirbyteLogger
from airbyte_cdk.models import SyncMode
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator

from .streams import (  # CustomObjectEvents,; Jobs,
    Limits,
    ObjectRecords,
    ObjectTypePolicies,
    ObjectTypes,
    RelationshipRecords,
    RelationshipTypes,
)


class HttpBasicAuthenticator(TokenAuthenticator):
    def __init__(self, auth: Tuple[str, str], auth_method: str = "Basic", **kwargs):
        auth_string = f"{auth[0]}:{auth[1]}".encode("utf8")
        b64_encoded = base64.b64encode(auth_string).decode("utf8")
        super().__init__(token=b64_encoded, auth_method=auth_method, **kwargs)


class SourceZendeskSunshine(AbstractSource):
    def check_connection(self, logger: AirbyteLogger, config: Mapping[str, Any]) -> Tuple[bool, Any]:
        try:
            pendulum.parse(config["start_date"], strict=True)
            authenticator = HttpBasicAuthenticator(auth=(f'{config["email"]}/token', config["api_token"]))
            stream = Limits(authenticator=authenticator, subdomain=config["subdomain"], start_date=pendulum.parse(config["start_date"]))
            records = stream.read_records(sync_mode=SyncMode.full_refresh)
            next(records)
            return True, None
        except Exception as e:
            return False, repr(e)

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        """
        CustomObjectEvents stream is an early access stream. (looks like it is a new feature)
        It requires activation in site ui + manual activation from Zendesk via call.
        I requested the call, but since they did not approve it,
        this endpoint will return 403 Forbidden. Thats why it is disabled here.

        Jobs stream is also commented out. Reason: It is dynamic.
        It can have the data, but this data have time to live.
        After this time is passed we have no data. It will require permanent population, to pass
        the test criteria `stream should contain at least 1 record)
        """
        authenticator = HttpBasicAuthenticator(auth=(f'{config["email"]}/token', config["api_token"]))
        args = {"authenticator": authenticator, "subdomain": config["subdomain"], "start_date": config["start_date"]}
        return [
            ObjectTypes(**args),
            ObjectRecords(**args),
            RelationshipTypes(**args),
            RelationshipRecords(**args),
            # CustomObjectEvents(**args),
            ObjectTypePolicies(**args),
            # Jobs(**args),
            Limits(**args),
        ]
