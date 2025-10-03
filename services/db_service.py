"""Database service for MongoDB operations."""
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pymongo import MongoClient, ASCENDING, IndexModel
from pymongo.errors import DuplicateKeyError, PyMongoError
from bson import ObjectId
from config import config


class DatabaseService:
    """Service for database operations."""
    
    def __init__(self, mongo_uri: Optional[str] = None, db_name: Optional[str] = None):
        """
        Initialize database service.
        
        Args:
            mongo_uri: MongoDB connection URI
            db_name: Database name
        """
        self.mongo_uri = mongo_uri or config.MONGO_URI
        self.db_name = db_name or config.MONGO_DB_NAME
        self.client: Optional[MongoClient] = None
        self.db = None
        
    def connect(self) -> None:
        """Establish database connection and create indexes."""
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.db = self.client[self.db_name]
            # Test connection
            self.client.server_info()
            self._create_indexes()
        except PyMongoError as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
    
    def _create_indexes(self) -> None:
        """Create necessary indexes for collections."""
        # Users collection indexes
        self.db.users.create_index([("username", ASCENDING)], unique=True)
        self.db.users.create_index([("email", ASCENDING)], unique=True)
        
        # Workouts collection indexes
        self.db.workouts.create_index([("user_id", ASCENDING)])
        self.db.workouts.create_index([("date", ASCENDING)])
        self.db.workouts.create_index([("user_id", ASCENDING), ("date", ASCENDING)])
        
        # Meals collection indexes
        self.db.meals.create_index([("user_id", ASCENDING)])
        self.db.meals.create_index([("time", ASCENDING)])
        self.db.meals.create_index([("user_id", ASCENDING), ("time", ASCENDING)])
        
        # Weight logs collection indexes
        self.db.weight_logs.create_index([("user_id", ASCENDING)])
        self.db.weight_logs.create_index([("date", ASCENDING)])
        self.db.weight_logs.create_index([("user_id", ASCENDING), ("date", ASCENDING)], unique=True)
    
    # User operations
    def create_user(self, user_data: Dict[str, Any]) -> str:
        """
        Create a new user.
        
        Args:
            user_data: User data dictionary
            
        Returns:
            Created user ID
            
        Raises:
            ValueError: If username or email already exists
        """
        try:
            user_data["created_at"] = datetime.utcnow()
            result = self.db.users.insert_one(user_data)
            return str(result.inserted_id)
        except DuplicateKeyError as e:
            if "username" in str(e):
                raise ValueError(f"Username '{user_data.get('username')}' already exists")
            elif "email" in str(e):
                raise ValueError(f"Email '{user_data.get('email')}' already exists")
            raise ValueError("User with this username or email already exists")
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User document or None
        """
        user = self.db.users.find_one({"username": username.lower()})
        if user:
            user["_id"] = str(user["_id"])
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User document or None
        """
        try:
            user = self.db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user["_id"] = str(user["_id"])
            return user
        except Exception:
            return None
    
    def delete_user(self, username: str) -> bool:
        """
        Delete user and all associated data.
        
        Args:
            username: Username
            
        Returns:
            True if deleted, False if user not found
        """
        user = self.get_user_by_username(username)
        if not user:
            return False
        
        user_id = user["_id"]
        
        # Delete user and all associated data
        self.db.users.delete_one({"_id": ObjectId(user_id)})
        self.db.workouts.delete_many({"user_id": user_id})
        self.db.meals.delete_many({"user_id": user_id})
        self.db.weight_logs.delete_many({"user_id": user_id})
        
        return True
    
    # Workout operations
    def create_workout(self, workout_data: Dict[str, Any]) -> str:
        """
        Create a new workout.
        
        Args:
            workout_data: Workout data dictionary
            
        Returns:
            Created workout ID
        """
        workout_data["created_at"] = datetime.utcnow()
        # Ensure date is stored as datetime for consistency
        if isinstance(workout_data.get("date"), date) and not isinstance(workout_data["date"], datetime):
            workout_data["date"] = datetime.combine(workout_data["date"], datetime.min.time())
        result = self.db.workouts.insert_one(workout_data)
        return str(result.inserted_id)
    
    def get_workouts(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get workouts for a user.
        
        Args:
            user_id: User ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Optional limit on results
            
        Returns:
            List of workout documents
        """
        query = {"user_id": user_id}
        
        if start_date or end_date:
            query["date"] = {}
            if start_date:
                query["date"]["$gte"] = datetime.combine(start_date, datetime.min.time())
            if end_date:
                query["date"]["$lte"] = datetime.combine(end_date, datetime.max.time())
        
        cursor = self.db.workouts.find(query).sort("date", -1)
        if limit:
            cursor = cursor.limit(limit)
        
        workouts = list(cursor)
        for workout in workouts:
            workout["_id"] = str(workout["_id"])
        return workouts
    
    def get_workout_by_id(self, workout_id: str) -> Optional[Dict[str, Any]]:
        """Get workout by ID."""
        try:
            workout = self.db.workouts.find_one({"_id": ObjectId(workout_id)})
            if workout:
                workout["_id"] = str(workout["_id"])
            return workout
        except Exception:
            return None
    
    def update_workout(self, workout_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a workout.
        
        Args:
            workout_id: Workout ID
            update_data: Fields to update
            
        Returns:
            True if updated, False if not found
        """
        try:
            # Convert date to datetime if needed
            if "date" in update_data and isinstance(update_data["date"], date):
                if not isinstance(update_data["date"], datetime):
                    update_data["date"] = datetime.combine(update_data["date"], datetime.min.time())
            
            result = self.db.workouts.update_one(
                {"_id": ObjectId(workout_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def delete_workout(self, workout_id: str) -> bool:
        """
        Delete a workout.
        
        Args:
            workout_id: Workout ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            result = self.db.workouts.delete_one({"_id": ObjectId(workout_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    # Meal operations
    def create_meal(self, meal_data: Dict[str, Any]) -> str:
        """
        Create a new meal.
        
        Args:
            meal_data: Meal data dictionary
            
        Returns:
            Created meal ID
        """
        meal_data["created_at"] = datetime.utcnow()
        result = self.db.meals.insert_one(meal_data)
        return str(result.inserted_id)
    
    def get_meals(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get meals for a user.
        
        Args:
            user_id: User ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Optional limit on results
            
        Returns:
            List of meal documents
        """
        query = {"user_id": user_id}
        
        if start_date or end_date:
            query["time"] = {}
            if start_date:
                query["time"]["$gte"] = datetime.combine(start_date, datetime.min.time())
            if end_date:
                query["time"]["$lte"] = datetime.combine(end_date, datetime.max.time())
        
        cursor = self.db.meals.find(query).sort("time", -1)
        if limit:
            cursor = cursor.limit(limit)
        
        meals = list(cursor)
        for meal in meals:
            meal["_id"] = str(meal["_id"])
        return meals
    
    def get_meal_by_id(self, meal_id: str) -> Optional[Dict[str, Any]]:
        """Get meal by ID."""
        try:
            meal = self.db.meals.find_one({"_id": ObjectId(meal_id)})
            if meal:
                meal["_id"] = str(meal["_id"])
            return meal
        except Exception:
            return None
    
    def update_meal(self, meal_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a meal.
        
        Args:
            meal_id: Meal ID
            update_data: Fields to update
            
        Returns:
            True if updated, False if not found
        """
        try:
            result = self.db.meals.update_one(
                {"_id": ObjectId(meal_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def delete_meal(self, meal_id: str) -> bool:
        """
        Delete a meal.
        
        Args:
            meal_id: Meal ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            result = self.db.meals.delete_one({"_id": ObjectId(meal_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    # Weight log operations
    def create_weight_log(self, weight_data: Dict[str, Any]) -> str:
        """
        Create a new weight log.
        
        Args:
            weight_data: Weight log data dictionary
            
        Returns:
            Created weight log ID
            
        Raises:
            ValueError: If weight log for this date already exists
        """
        try:
            weight_data["created_at"] = datetime.utcnow()
            # Ensure date is stored as datetime for consistency
            if isinstance(weight_data.get("date"), date) and not isinstance(weight_data["date"], datetime):
                weight_data["date"] = datetime.combine(weight_data["date"], datetime.min.time())
            result = self.db.weight_logs.insert_one(weight_data)
            return str(result.inserted_id)
        except DuplicateKeyError:
            raise ValueError(f"Weight log for date {weight_data.get('date')} already exists")
    
    def get_weight_logs(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get weight logs for a user.
        
        Args:
            user_id: User ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Optional limit on results
            
        Returns:
            List of weight log documents
        """
        query = {"user_id": user_id}
        
        if start_date or end_date:
            query["date"] = {}
            if start_date:
                query["date"]["$gte"] = datetime.combine(start_date, datetime.min.time())
            if end_date:
                query["date"]["$lte"] = datetime.combine(end_date, datetime.max.time())
        
        cursor = self.db.weight_logs.find(query).sort("date", -1)
        if limit:
            cursor = cursor.limit(limit)
        
        logs = list(cursor)
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs
    
    def get_weight_log_by_id(self, log_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a weight log by ID.
        
        Args:
            log_id: Weight log ID
            
        Returns:
            Weight log document or None if not found
        """
        try:
            log = self.db.weight_logs.find_one({"_id": ObjectId(log_id)})
            if log:
                log["_id"] = str(log["_id"])
            return log
        except Exception:
            return None


# Global database service instance
db_service = DatabaseService()
