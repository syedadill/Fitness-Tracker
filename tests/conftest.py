"""Pytest configuration and fixtures."""
import pytest
from datetime import date, datetime
import mongomock
from fakeredis import FakeRedis
from services.db_service import DatabaseService
from services.cache_service import CacheService
from services.report_service import ReportService


@pytest.fixture
def mock_db():
    """Create a mock database service."""
    # Use mongomock for testing
    db = DatabaseService(mongo_uri="mongodb://localhost:27017/", db_name="test_fitness_tracker")
    db.client = mongomock.MongoClient()
    db.db = db.client["test_fitness_tracker"]
    db._create_indexes()
    yield db
    # Cleanup
    db.client.drop_database("test_fitness_tracker")
    db.disconnect()


@pytest.fixture
def mock_cache():
    """Create a mock cache service."""
    cache = CacheService(redis_url="redis://localhost:6379/0", ttl=300)
    cache.client = FakeRedis(decode_responses=True)
    yield cache
    cache.client.flushall()
    cache.disconnect()


@pytest.fixture
def mock_report_service(mock_db, mock_cache):
    """Create a report service with mock dependencies."""
    service = ReportService()
    service.db = mock_db
    service.cache = mock_cache
    return service


@pytest.fixture
def sample_user(mock_db):
    """Create a sample user for testing."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "goals": {
            "target_weight": 75.0,
            "weekly_workout_minutes": 150
        }
    }
    user_id = mock_db.create_user(user_data)
    user_data["_id"] = user_id
    return user_data


@pytest.fixture
def sample_workout(mock_db, sample_user):
    """Create a sample workout for testing."""
    workout_data = {
        "user_id": sample_user["_id"],
        "type": "running",
        "duration_minutes": 30,
        "intensity": "medium",
        "date": date(2025, 10, 1)
    }
    workout_id = mock_db.create_workout(workout_data)
    workout_data["_id"] = workout_id
    return workout_data


@pytest.fixture
def sample_meal(mock_db, sample_user):
    """Create a sample meal for testing."""
    meal_data = {
        "user_id": sample_user["_id"],
        "name": "Breakfast",
        "calories": 500,
        "macros": {
            "protein": 30.0,
            "carbs": 50.0,
            "fat": 15.0
        },
        "time": datetime(2025, 10, 1, 8, 0)
    }
    meal_id = mock_db.create_meal(meal_data)
    meal_data["_id"] = meal_id
    return meal_data


@pytest.fixture
def sample_weight_log(mock_db, sample_user):
    """Create a sample weight log for testing."""
    weight_data = {
        "user_id": sample_user["_id"],
        "weight_kg": 80.0,
        "date": date(2025, 10, 1)
    }
    log_id = mock_db.create_weight_log(weight_data)
    weight_data["_id"] = log_id
    return weight_data
