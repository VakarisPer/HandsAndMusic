"""Spawn scheduler for chart events."""

from src.domain.models import ChartEvent, Note


class SpawnSystem:
    """Spawns notes from chart events using a fixed time lookahead."""

    def __init__(self, spawn_offset_seconds: float) -> None:
        self.spawn_offset_seconds = spawn_offset_seconds
        self._next_event_index = 0

    def reset(self) -> None:
        self._next_event_index = 0

    def spawn_due_notes(self, events: list[ChartEvent], current_time: float) -> list[Note]:
        spawned: list[Note] = []
        while self._next_event_index < len(events):
            event = events[self._next_event_index]
            if current_time < (event.time_seconds - self.spawn_offset_seconds):
                break
            spawned.append(
                Note(
                    lane=event.lane,
                    scheduled_time=event.time_seconds,
                    y=-40.0,
                    kind=event.kind,
                    spawned=True,
                )
            )
            self._next_event_index += 1
        return spawned

