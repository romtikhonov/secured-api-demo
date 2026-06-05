import asyncio

from database.models import User, UserProfile
from database.session import SessionLocal
from demos.query_counter import QueryCounter
from sqlalchemy import select


async def demonstrate_nplusone_problem():
    async with SessionLocal() as session:
        with QueryCounter() as qc:
            # Получаем всех пользователей (1 запрос)
            result = await session.execute(select(User))
            users = result.scalars().all()

            print(f"After loading users: {qc.query_count} queries")

            # Имитируем N+1: отдельный запрос для каждого профиля
            for user in users:
                profile = await session.get(UserProfile, user.id)  # ← Отдельный запрос!
                if profile:
                    print(f"User: {user.username}, Profile: {profile.bio[:20]}...")

            print(f"Total queries with N+1: {qc.query_count}")
            print(f"Number of users: {len(users)}")


async def demonstrate_optimized_loading():
    async with SessionLocal() as session:
        with QueryCounter() as qc:
            # Загружаем пользователей с профилями одним дополнительным запросом
            result = await session.execute(select(User))
            users = result.scalars().all()

            print(f"After optimized loading: {qc.query_count} queries")

            # Выводим данные (без дополнительных запросов!)
            for user in users:
                if user.profile:
                    print(f"User: {user.username}, Profile: {user.profile.bio[:20]}...")

            print(f"Total queries with optimization: {qc.query_count}")


if __name__ == "__main__":
    asyncio.run(demonstrate_optimized_loading())
