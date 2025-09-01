"""Отслеживание прогресса обработки."""
import logging

logger = logging.getLogger(__name__)

class ProgressTracker:
    def __init__(self, total: int, unit: str = "items", log_steps: int = 10):
        self.total = total
        self.unit = unit
        self.step = max(1, total // log_steps)
    
    def update(self, current: int) -> None:
        if current % self.step == 0 or current == self.total:
            percent = int(current / self.total * 100)
            logger.info(f"Processed {current}/{self.total} {self.unit} ({percent}%)")
