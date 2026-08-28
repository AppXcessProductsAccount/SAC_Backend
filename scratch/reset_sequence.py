import asyncio
from sqlalchemy import text
from app.core.database import engine

async def reset_sequence():
    async with engine.begin() as conn:
        print("Checking max id in sections table...")
        result = await conn.execute(text("SELECT MAX(id) FROM sections"))
        max_id = result.scalar()
        print(f"Max ID: {max_id}")
        
        if max_id is not None:
            print(f"Resetting sections_id_seq to {max_id}...")
            await conn.execute(text(f"SELECT setval('sections_id_seq', {max_id})"))
            print("Sequence reset successfully.")
        else:
            print("Sections table is empty, no reset needed.")

if __name__ == "__main__":
    asyncio.run(reset_sequence())
