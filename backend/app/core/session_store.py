"""In-memory session store. User datasets live in RAM only and are never persisted."""
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd


@dataclass
class Session:
    dataset_id: str
    filename: str
    df: pd.DataFrame
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    history: list = field(default_factory=list)


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def create(self, df: pd.DataFrame, filename: str) -> Session:
        dataset_id = uuid.uuid4().hex[:12]
        session = Session(dataset_id=dataset_id, filename=filename, df=df)
        with self._lock:
            self._sessions[dataset_id] = session
        return session

    def get(self, dataset_id: str) -> Session | None:
        return self._sessions.get(dataset_id)

    def delete(self, dataset_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(dataset_id, None) is not None


store = SessionStore()
