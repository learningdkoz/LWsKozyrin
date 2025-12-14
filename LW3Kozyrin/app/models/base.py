"""
Базовый класс для всех моделей SQLAlchemy
"""
from sqlalchemy.orm import declarative_base

# Единый Base для всех моделей - это критично для правильной работы relationship
Base = declarative_base()
