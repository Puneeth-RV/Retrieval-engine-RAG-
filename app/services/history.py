from collections import defaultdict, deque
from threading import Lock

MAX_TURNS = 6

_store: dict[str, deque] = defaultdict(lambda: deque(maxlen=MAX_TURNS))
_lock = Lock()


def get_history(session_id: str) -> list[tuple[str, str]]:
    with _lock:
        return list(_store[session_id])


def append_turn(session_id: str, question: str, answer: str) -> None:
    with _lock:
        _store[session_id].append((question, answer))
