from pathlib import Path

from edge.main import run_once


def test_run_once_demo_enqueues_event(tmp_path: Path) -> None:
    enqueued = run_once(demo_event=True, queue_db_path=str(tmp_path / "queue.db"))
    assert enqueued >= 1
