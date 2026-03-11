from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import pytest
from httpx import AsyncClient
from app import app

@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests():
    load_dotenv()
    
@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
        
@pytest.fixture
async def setup_db():
    # Setup: Connect to MongoDB and clear test collection
    from app import db_helper, DB_NAME
    db_helper.client = AsyncIOMotorClient("mongodb://localhost:27017")
    db_helper.db = db_helper.client[DB_NAME]
    await db_helper.db["test_collection"].delete_many({})
    yield
    # Teardown: Close MongoDB connection
    db_helper.client.close()