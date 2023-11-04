"""
Author: Erez Drutin
Date: 04.11.2023
Purpose: A file populated with models that will be used throughout the
entire code-base. Normally this would be separated into files and directories
based on functionality. However, in this case this seemed "excessive"
compared to the requirements as is.
"""

from dataclasses import dataclass
from typing import List
from datetime import datetime
from const import RequestCodes, ResponseCodes


@dataclass
class Client:
    id: bytes
    name: str
    public_key: bytes
    last_seen: datetime
    aes_key: bytes


@dataclass
class File:
    id: bytes
    file_name: str
    path_name: str
    verified: bool


@dataclass
class ServerState:
    clients: List[Client]
    files: List[File]


@dataclass
class Request:
    client_id: bytes
    version: str
    code: RequestCodes
    payload_size: int
    payload: bytes


@dataclass
class Response:
    version: str
    code: ResponseCodes
    payload: bytes

    @property
    def payload_size(self):
        return len(self.payload)

    def to_bytes(self) -> bytes:
        """
        Converts the response details dataclass into a byte sequence which
        will in turn be sent to the Client.
        @return: A bytes sequence.
        """
        version_bytes = self.version.encode('utf-8')
        code_bytes = self.code.value.to_bytes(2, byteorder='big')
        payload_size_bytes = self.payload_size.to_bytes(4, byteorder='big')
        return version_bytes + code_bytes + payload_size_bytes + self.payload
