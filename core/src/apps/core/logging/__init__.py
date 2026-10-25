from .logging import setup_logging
from .logger import get_logger

"""
Настроенный логгер

Пожалуйста, везде в приложении используйте логгер единым образом:

```py
from src.apps.core.logging import get_logger

logger = get_logger(__name__)
logger.info("Application '%s' v%s initialized",
            "Hello app", "1.0.0")
```
"""
