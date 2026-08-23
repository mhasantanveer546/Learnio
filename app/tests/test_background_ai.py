import time
from app.services.background_ai import run_background_task


def test_background_task_runs_async(app):
    result = []

    def slow_task():
        time.sleep(0.1)
        result.append("done")

    with app.app_context():
        thread = run_background_task(slow_task)
        assert thread.is_alive() or result == ["done"]

    time.sleep(0.2)
    assert result == ["done"]