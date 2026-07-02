import re

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, declared_attr, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _pluralize(word: str) -> str:
    if word.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"
    if word.endswith("y") and word[-2:-1] not in "aeiou":
        return word[:-1] + "ies"
    return word + "s"


class Base(DeclarativeBase):
    """Every model gets its table name for free: CamelCase class name ->
    snake_case, pluralized (e.g. `TrialUser` -> `trial_users`), instead of
    each model repeating an explicit `__tablename__`.
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        snake_case = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return _pluralize(snake_case)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
