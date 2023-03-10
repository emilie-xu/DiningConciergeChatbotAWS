# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.
#
# Modifications Copyright OpenSearch Contributors. See
# GitHub history for details.
#
#  Licensed to Elasticsearch B.V. under one or more contributor
#  license agreements. See the NOTICE file distributed with
#  this work for additional information regarding copyright
#  ownership. Elasticsearch B.V. licenses this file to you under
#  the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.


# flake8: noqa
from __future__ import absolute_import

import logging
import re
import sys
import warnings

from ._version import __versionstr__

_major, _minor, _patch = [
    int(x) for x in re.search(r"^(\d+)\.(\d+)\.(\d+)", __versionstr__).groups()
]
VERSION = __version__ = (_major, _minor, _patch)

logger = logging.getLogger("opensearch")
logger.addHandler(logging.NullHandler())

from .client import OpenSearch
from .connection import Connection, RequestsHttpConnection, Urllib3HttpConnection
from .connection_pool import ConnectionPool, ConnectionSelector, RoundRobinSelector
from .exceptions import (
    AuthenticationException,
    AuthorizationException,
    ConflictError,
    ConnectionError,
    ConnectionTimeout,
    ImproperlyConfigured,
    NotFoundError,
    OpenSearchDeprecationWarning,
    OpenSearchException,
    OpenSearchWarning,
    RequestError,
    SerializationError,
    SSLError,
    TransportError,
)
from .helpers import AWSV4SignerAsyncAuth, AWSV4SignerAuth
from .serializer import JSONSerializer
from .transport import Transport

# Only raise one warning per deprecation message so as not
# to spam up the user if the same action is done multiple times.
warnings.simplefilter("default", category=OpenSearchDeprecationWarning, append=True)

__all__ = [
    "OpenSearch",
    "Transport",
    "ConnectionPool",
    "ConnectionSelector",
    "RoundRobinSelector",
    "JSONSerializer",
    "Connection",
    "RequestsHttpConnection",
    "AsyncHttpConnection",
    "Urllib3HttpConnection",
    "ImproperlyConfigured",
    "OpenSearchException",
    "SerializationError",
    "TransportError",
    "NotFoundError",
    "ConflictError",
    "RequestError",
    "ConnectionError",
    "SSLError",
    "ConnectionTimeout",
    "AuthenticationException",
    "AuthorizationException",
    "OpenSearchWarning",
    "OpenSearchDeprecationWarning",
    "AWSV4SignerAuth",
    "AWSV4SignerAsyncAuth",
]

try:
    # Asyncio only supported on Python 3.6+
    if sys.version_info < (3, 6):
        raise ImportError

    from ._async.client import AsyncOpenSearch
    from ._async.http_aiohttp import AIOHttpConnection, AsyncConnection
    from ._async.transport import AsyncTransport
    from .connection import AsyncHttpConnection

    __all__ += [
        "AIOHttpConnection",
        "AsyncConnection",
        "AsyncTransport",
        "AsyncOpenSearch",
        "AsyncHttpConnection",
    ]
except (ImportError, SyntaxError):
    pass
