"""Medição leve da inicialização do ambiente."""

from __future__ import annotations

from time import perf_counter

from devtools.logger import Logger


class Profiler:
    def __init__(self) -> None:
        self.start_time: float | None = None
        self.marks: dict[str, float] = {}

    def start(self) -> None:
        self.start_time = perf_counter()
        self.marks.clear()

    def mark(self, name: str) -> None:
        if self.start_time is not None:
            self.marks[name] = perf_counter() - self.start_time

    def finish_startup(self, state) -> float:
        elapsed = self.elapsed()
        state.register_startup(elapsed)
        Logger.success(f"Inicialização do DevTools: {elapsed:.3f}s")
        return elapsed

    def elapsed(self) -> float:
        return 0.0 if self.start_time is None else perf_counter() - self.start_time

    def report(self) -> dict[str, object]:
        return {"total": self.elapsed(), "marks": self.marks.copy()}

    def print_report(self) -> None:
        report = self.report()
        lines = [f"Tempo total: {report['total']:.3f}s"]
        lines.extend(f"{name}: {elapsed:.3f}s" for name, elapsed in self.marks.items())
        Logger.box("PROFILE", *lines)
