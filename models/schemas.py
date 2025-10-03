"""Pydantic models for data validation and MongoDB schemas."""
from datetime import datetime
from datetime import date as date_type
from typing import Optional, Literal
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v, _info=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class FitnessGoals(BaseModel):
    """User fitness goals."""
    target_weight: Optional[float] = Field(None, gt=0, description="Target weight in kg")
    weekly_workout_minutes: Optional[int] = Field(None, ge=0, description="Weekly workout goal in minutes")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "target_weight": 75.0,
            "weekly_workout_minutes": 150
        }
    })


class UserBase(BaseModel):
    """Base user model for creation."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    dob: Optional[date_type] = Field(None, description="Date of birth")
    goals: Optional[FitnessGoals] = Field(default_factory=FitnessGoals, description="Fitness goals")
    
    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores and hyphens allowed)')
        return v.lower()
    
    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        return v.lower()


class UserCreate(UserBase):
    """Model for creating a new user."""
    pass


class User(UserBase):
    """Complete user model with database fields."""
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class WorkoutBase(BaseModel):
    """Base workout model."""
    type: str = Field(..., min_length=1, max_length=50, description="Type of workout (e.g., running, cycling)")
    duration_minutes: int = Field(..., gt=0, description="Workout duration in minutes")
    intensity: Literal["low", "medium", "high"] = Field(..., description="Workout intensity level")
    date: date_type = Field(..., description="Workout date")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    
    @field_validator('date')
    @classmethod
    def date_not_future(cls, v: date_type) -> date_type:
        if v > date_type.today():
            raise ValueError('Workout date cannot be in the future')
        return v


class WorkoutCreate(WorkoutBase):
    """Model for creating a new workout."""
    user_id: str = Field(..., description="User ID")


class Workout(WorkoutBase):
    """Complete workout model with database fields."""
    id: str = Field(alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class MacroNutrients(BaseModel):
    """Macronutrient breakdown."""
    protein: float = Field(..., ge=0, description="Protein in grams")
    carbs: float = Field(..., ge=0, description="Carbohydrates in grams")
    fat: float = Field(..., ge=0, description="Fat in grams")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "protein": 25.0,
            "carbs": 40.0,
            "fat": 15.0
        }
    })


class MealBase(BaseModel):
    """Base meal model."""
    name: str = Field(..., min_length=1, max_length=100, description="Meal name")
    calories: int = Field(..., gt=0, description="Total calories")
    macros: MacroNutrients = Field(..., description="Macronutrient breakdown")
    time: datetime = Field(..., description="Meal time")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    
    @field_validator('time')
    @classmethod
    def time_not_future(cls, v: datetime) -> datetime:
        # Handle both naive and timezone-aware datetimes
        # For naive datetimes, assume they are in user's local time
        now = datetime.now() if v.tzinfo is None else datetime.utcnow()
        if v > now:
            raise ValueError('Meal time cannot be in the future')
        return v


class MealCreate(MealBase):
    """Model for creating a new meal."""
    user_id: str = Field(..., description="User ID")


class Meal(MealBase):
    """Complete meal model with database fields."""
    id: str = Field(alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class WeightLogBase(BaseModel):
    """Base weight log model."""
    weight_kg: float = Field(..., gt=0, le=500, description="Body weight in kilograms")
    date: date_type = Field(..., description="Date of weight measurement")
    
    @field_validator('date')
    @classmethod
    def date_not_future(cls, v: date_type) -> date_type:
        if v > date_type.today():
            raise ValueError('Weight log date cannot be in the future')
        return v


class WeightLogCreate(WeightLogBase):
    """Model for creating a new weight log."""
    user_id: str = Field(..., description="User ID")


class WeightLog(WeightLogBase):
    """Complete weight log model with database fields."""
    id: str = Field(alias="_id")
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class WorkoutUpdate(BaseModel):
    """Model for updating workout fields."""
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    duration_minutes: Optional[int] = Field(None, gt=0)
    intensity: Optional[Literal["low", "medium", "high"]] = None
    date: Optional[date_type] = None
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('date')
    @classmethod
    def date_not_future(cls, v: Optional[date_type]) -> Optional[date_type]:
        if v and v > date_type.today():
            raise ValueError('Workout date cannot be in the future')
        return v


class MealUpdate(BaseModel):
    """Model for updating meal fields."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    calories: Optional[int] = Field(None, gt=0)
    macros: Optional[MacroNutrients] = None
    time: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('time')
    @classmethod
    def time_not_future(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v > datetime.utcnow():
            raise ValueError('Meal time cannot be in the future')
        return v
