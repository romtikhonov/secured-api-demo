import logging


class QueryCountHandler(logging.Handler):
    def __init__(self, counter_callback):
        super().__init__()
        self.counter_callback = counter_callback

    def emit(self, record):
        self.counter_callback()


class QueryCounter:
    def __init__(self):
        self._query_count: int = 0
        self._logger = None
        self._original_level = None
        self._handler = None

    @property
    def query_count(self) -> int:
        return self._query_count

    def _increment_counter(self):
        self._query_count += 1

    def __enter__(self):
        self._logger = logging.getLogger("sqlalchemy.engine")
        self._original_level = self._logger.level
        self._logger.setLevel(logging.INFO)
        self._handler = QueryCountHandler(counter_callback=self._increment_counter)
        self._logger.addHandler(self._handler)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._logger is not None:
            self._logger.setLevel(self._original_level)
            self._logger.removeHandler(self._handler)
            self._handler = None
            self._logger = None
            self._original_level = None


if __name__ == "__main__":
    from database.models import User
    from database.session import SessionLocal
    from sqlalchemy import select

    async def test_simple():
        # Создаём чистую сессию
        async with SessionLocal() as session:
            # Начинаем транзакцию явно
            await session.begin()

            with QueryCounter() as qc:
                # Один запрос
                await session.execute(select(User))
                count1 = qc.query_count

                # Второй запрос
                await session.execute(select(User))
                count2 = qc.query_count

            await session.rollback()  # Отменяем транзакцию

            print(f"First SELECT added: {count1} queries")
            print(f"Second SELECT added: {count2 - count1} queries")

    import asyncio

    asyncio.run(test_simple())
