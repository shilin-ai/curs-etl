"""Общие константы для обработки текста."""

class ChunkingDefaults:
    SIZE = 1000
    OVERLAP = 200
    SEPARATORS = ["\n\n", "\n", " ", ""]

class ValidationRules:
    MIN_TEXT_LENGTH = 1
    MAX_TEXT_LENGTH = 50000

class LoggingConfig:
    PROGRESS_STEPS = 10
