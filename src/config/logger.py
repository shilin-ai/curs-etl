import logging
import sys
from pathlib import Path
from config.settings import settings

# Настраивает и возвращает логгер с заданным именем и уровнем
def setup_logger(name: str = "confluence_bot", level: str = None) -> logging.Logger:
    """
    Настраивает и возвращает логгер с указанным именем и уровнем
    
    Args:
        name: Имя логгера
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging.Logger: Настроенный логгер
    """
    try:
        # Определяем уровень логирования
        if level is None:
            level = getattr(settings, 'log_level', 'INFO')
        
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Создаем логгер
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        
        # Очищаем существующие обработчики
        logger.handlers.clear()
        
        # Создаем форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Обработчик для вывода в консоль (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
        
    except Exception as e:
        # Fallback к базовому логгеру в случае ошибки
        print(f"Error setting up logger '{name}': {e}")
        fallback_logger = logging.getLogger(name)
        if not fallback_logger.handlers:
            fallback_logger.addHandler(logging.StreamHandler(sys.stdout))
        return fallback_logger

# Возвращает существующий логгер или создает новый, если его нет
def get_logger(name: str = "confluence_bot") -> logging.Logger:
    """
    Возвращает существующий логгер или создает новый
    
    Args:
        name: Имя логгера
    
    Returns:
        logging.Logger: Логгер
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
