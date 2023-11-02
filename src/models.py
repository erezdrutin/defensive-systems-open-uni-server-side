import datetime
from dataclasses import dataclass
from typing import List
from datetime import datetime


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
