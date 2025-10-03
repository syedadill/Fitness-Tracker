"""Main CLI application for Fitness Tracker."""
import sys
from datetime import datetime, date
from typing import Optional
import click
from pydantic import ValidationError

from config import config
from models.schemas import (
    UserCreate, WorkoutCreate, MealCreate, WeightLogCreate,
    WorkoutUpdate, MealUpdate, MacroNutrients, FitnessGoals
)
from services.db_service import db_service
from services.cache_service import cache_service
from services.report_service import report_service


def init_services():
    """Initialize database and cache services."""
    try:
        db_service.connect()
        try:
            cache_service.connect()
        except Exception as e:
            click.echo(f"Warning: Redis connection failed: {e}", err=True)
            click.echo("Continuing without cache support...", err=True)
    except Exception as e:
        click.echo(f"Error: Failed to connect to database: {e}", err=True)
        sys.exit(1)


def cleanup_services():
    """Cleanup service connections."""
    db_service.disconnect()
    cache_service.disconnect()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Fitness Tracker - Track your workouts, meals, and progress."""
    pass


@cli.command()
@click.option('--username', required=True, help='Unique username')
@click.option('--email', required=True, help='User email address')
@click.option('--full-name', help='Full name')
@click.option('--dob', help='Date of birth (YYYY-MM-DD)')
@click.option('--target-weight', type=float, help='Target weight in kg')
@click.option('--weekly-minutes', type=int, help='Weekly workout goal in minutes')
def register(username, email, full_name, dob, target_weight, weekly_minutes):
    """Register a new user."""
    init_services()
    
    try:
        # Prepare user data
        user_data = {
            "username": username,
            "email": email,
        }
        
        if full_name:
            user_data["full_name"] = full_name
        
        if dob:
            try:
                user_data["dob"] = datetime.strptime(dob, "%Y-%m-%d").date()
            except ValueError:
                click.echo("Error: Invalid date format. Use YYYY-MM-DD", err=True)
                sys.exit(1)
        
        # Handle goals
        goals = {}
        if target_weight is not None:
            goals["target_weight"] = target_weight
        if weekly_minutes is not None:
            goals["weekly_workout_minutes"] = weekly_minutes
        
        if goals:
            user_data["goals"] = goals
        
        # Validate with Pydantic
        user = UserCreate(**user_data)
        
        # Create user
        user_id = db_service.create_user(user.model_dump(exclude_none=True))
        
        click.echo(f"✅ User '{username}' registered successfully!")
        click.echo(f"User ID: {user_id}")
        
    except ValidationError as e:
        click.echo("Validation error:", err=True)
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            click.echo(f"  {field}: {error['msg']}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)
    finally:
        cleanup_services()


@cli.command()
@click.option('--user', required=True, help='Username')
@click.option('--type', 'workout_type', required=True, help='Workout type (e.g., running, cycling)')
@click.option('--duration', required=True, type=int, help='Duration in minutes')
@click.option('--intensity', required=True, type=click.Choice(['low', 'medium', 'high']), help='Workout intensity')
@click.option('--date', 'workout_date', required=True, help='Workout date (YYYY-MM-DD)')
@click.option('--notes', help='Additional notes')
def add_workout(user, workout_type, duration, intensity, workout_date, notes):
    """Log a new workout."""
    init_services()
    
    try:
        # Get user
        user_doc = db_service.get_user_by_username(user)
        if not user_doc:
            click.echo(f"Error: User '{user}' not found", err=True)
            sys.exit(1)
        
        # Parse date
        try:
            workout_date_obj = datetime.strptime(workout_date, "%Y-%m-%d").date()
        except ValueError:
            click.echo("Error: Invalid date format. Use YYYY-MM-DD", err=True)
            sys.exit(1)
        
        # Prepare workout data
        workout_data = {
            "user_id": user_doc["_id"],
            "type": workout_type,
            "duration_minutes": duration,
            "intensity": intensity,
            "date": workout_date_obj
        }
        
        if notes:
            workout_data["notes"] = notes
        
        # Validate with Pydantic
        workout = WorkoutCreate(**workout_data)
        
        # Create workout
        workout_id = db_service.create_workout(workout.model_dump())
        
        # Invalidate user's report cache
        report_service.invalidate_user_cache(user_doc["_id"])
        
        click.echo(f"✅ Workout logged successfully!")
        click.echo(f"Workout ID: {workout_id}")
        
    except ValidationError as e:
        click.echo("Validation error:", err=True)
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            click.echo(f"  {field}: {error['msg']}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        cleanup_services()


@cli.command()
@click.option('--user', required=True, help='Username')
@click.option('--from', 'from_date', help='Start date (YYYY-MM-DD)')
@click.option('--to', 'to_date', help='End date (YYYY-MM-DD)')
@click.option('--limit', type=int, help='Maximum number of results')
def list_workouts(user, from_date, to_date, limit):
    """List workouts for a user."""
    init_services()
    
    try:
        # Get user
        user_doc = db_service.get_user_by_username(user)
        if not user_doc:
            click.echo(f"Error: User '{user}' not found", err=True)
            sys.exit(1)
        
        # Parse dates
        start_date = None
        end_date = None
        
        if from_date:
            try:
                start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            except ValueError:
                click.echo("Error: Invalid from date format. Use YYYY-MM-DD", err=True)
                sys.exit(1)
        
        if to_date:
            try:
                end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
            except ValueError:
                click.echo("Error: Invalid to date format. Use YYYY-MM-DD", err=True)
                sys.exit(1)
        
        # Get workouts
        workouts = db_service.get_workouts(user_doc["_id"], start_date, end_date, limit)
        
        if not workouts:
            click.echo("No workouts found.")
            return
        
        click.echo(f"\n📋 Workouts for {user}:")
        click.echo("=" * 80)
        
        for workout in workouts:
            workout_date = workout["date"]
            if isinstance(workout_date, datetime):
                workout_date = workout_date.date()
            
            click.echo(f"\nID: {workout['_id']}")
            click.echo(f"Date: {workout_date}")
            click.echo(f"Type: {workout['type']}")
            click.echo(f"Duration: {workout['duration_minutes']} minutes")
            click.echo(f"Intensity: {workout['intensity']}")
            if workout.get('notes'):
                click.echo(f"Notes: {workout['notes']}")
        
        click.echo("\n" + "=" * 80)
        click.echo(f"Total: {len(workouts)} workout(s)")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        cleanup_services()


@cli.command()
@click.option('--id', 'workout_id', required=True, help='Workout ID')
@click.option('--type', 'workout_type', help='Workout type')
@click.option('--duration', type=int, help='Duration in minutes')
@click.option('--intensity', type=click.Choice(['low', 'medium', 'high']), help='Workout intensity')
@click.option('--date', 'workout_date', help='Workout date (YYYY-MM-DD)')
@click.option('--notes', help='Additional notes')
def update_workout(workout_id, workout_type, duration, intensity, workout_date, notes):
    """Update an existing workout."""
    init_services()
    
    try:
        # Get workout
        workout = db_service.get_workout_by_id(workout_id)
        if not workout:
            click.echo(f"Error: Workout '{workout_id}' not found", err=True)
            sys.exit(1)
        
        # Prepare update data
        update_data = {}
        
        if workout_type:
            update_data["type"] = workout_type
        if duration:
            update_data["duration_minutes"] = duration
        if intensity:
            update_data["intensity"] = intensity
        if workout_date:
            try:
                update_data["date"] = datetime.strptime(workout_date, "%Y-%m-%d").date()
            except ValueError:
                click.echo("Error: Invalid date format. Use YYYY-MM-DD", err=True)
                sys.exit(1)
        if notes is not None:  # Allow empty string to clear notes
            update_data["notes"] = notes
        
        if not update_data:
            click.echo("Error: No fields to update", err=True)
            sys.exit(1)
        
        # Validate with Pydantic
        WorkoutUpdate(**update_data)
        
        # Update workout
        success = db_service.update_workout(workout_id, update_data)
        
        if success:
            # Invalidate user's report cache
            report_service.invalidate_user_cache(workout["user_id"])
            click.echo("✅ Workout updated successfully!")
        else:
            click.echo("Error: Failed to update workout", err=True)
            sys.exit(1)
        
    except ValidationError as e:
        click.echo("Validation error:", err=True)
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            click.echo(f"  {field}: {error['msg']}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        cleanup_services()


@cli.command()
@click.option('--id', 'workout_id', required=True, help='Workout ID')
@click.confirmation_option(prompt='Are you sure you want to delete this workout?')
def delete_workout(workout_id):
    """Delete a workout."""
    init_services()
    
    try:
        # Get workout to get user_id for cache invalidation
        workout = db_service.get_workout_by_id(workout_id)
        if not workout:
            click.echo(f"Error: Workout '{workout_id}' not found", err=True)
            sys.exit(1)
        
        # Delete workout
        success = db_service.delete_workout(workout_id)
        
        if success:
            # Invalidate user's report cache
            report_service.invalidate_user_cache(workout["user_id"])
            click.echo("✅ Workout deleted successfully!")
        else:
            click.echo("Error: Failed to delete workout", err=True)
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        cleanup_services()


@cli.command()
@click.option('--user', required=True, help='Username')
@click.option('--name', required=True, help='Meal name')
@click.option('--calories', required=True, type=int, help='Total calories')
@click.option('--protein', required=True, type=float, help='Protein in grams')
@click.option('--carbs', required=True, type=float, help='Carbohydrates in grams')
@click.option('--fat', required=True, type=float, help='Fat in grams')
@click.option('--time', 'meal_time', required=True, help='Meal time (YYYY-MM-DD HH:MM)')
@click.option('--notes', help='Additional notes')
def add_meal(user, name, calories, protein, carbs, fat, meal_time, notes):
    """Log a new meal."""
    init_services()
    
    try:
        # Get user
        user_doc = db_service.get_user_by_username(user)
        if not user_doc:
            click.echo(f"Error: User '{user}' not found", err=True)
            sys.exit(1)
        
        # Parse time
        try:
            meal_time_obj = datetime.strptime(meal_time, "%Y-%m-%d %H:%M")
        except ValueError:
            click.echo("Error: Invalid time format. Use YYYY-MM-DD HH:MM", err=True)
            sys.exit(1)
        
        # Prepare meal data
        meal_data = {
            "user_id": user_doc["_id"],
            "name": name,
            "calories": calories,
            "macros": {
                "protein": protein,
                "carbs": carbs,
                "fat": fat
            },
            "time": meal_time_obj
        }
        
        if notes:
            meal_data["notes"] = notes
        
        # Validate with Pydantic
        meal = MealCreate(**meal_data)
        
        # Create meal
        meal_id = db_service.create_meal(meal.model_dump())
        
        # Invalidate user's report cache
        report_service.invalidate_user_cache(user_doc["_id"])
        
        click.echo(f"✅ Meal logged successfully!")
        click.echo(f"Meal ID: {meal_id}")
        
    except ValidationError as e:
        click.echo("Validation error:", err=True)
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            click.echo(f"  {field}: {error['msg']}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        cleanup_services()


@cli.command()
@click.option('--user', required=True, help='Username')
@click.option('--from', 'from_date', help='Start date (YYYY-MM-DD)')
@click.option('--to', 'to_date', help='End date (YYYY-MM-DD)')
@click.option('--limit', type=int, help='Maximum number of results')
def list_meals(user, from_date, to_date, limit):
    """List meals for a user."""
    init_services()
    
    try:
        # Get user
        user_doc = db_service.get_user_by_username(user)
        if not user_doc:
            click.echo(f"Error: User '{user}' not found", err=True)
            sys.exit(1)
        
        # Parse dates
        start_date = None
        end_date = None
        
        if from_date:
            try:
                start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            except ValueError:
                click.echo("Error: Invalid from date format. Use YYYY-MM-DD", err=True)
                sys.exit(1)
        
        if to_date:
            try:
                end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
            except ValueError:
                click.echo("Error: Invalid to date format. Use YYYY-MM-DD", err=True)
                sys.exit(1)
        
        # Get meals
        meals = db_service.get_meals(user_doc["_id"], start_date, end_date, limit)
        
        if not meals:
            click.echo("No meals found.")
            return
        
        click.echo(f"\n🍽️ Meals for {user}:")
        click.echo("=" * 80)
        
        for meal in meals:
            click.echo(f"\nID: {meal['_id']}")
            click.echo(f"Time: {meal['time']}")
            click.echo(f"Name: {meal['name']}")
            click.echo(f"Calories: {meal['calories']}")
            macros = meal['macros']
            click.echo(f"Macros: P:{macros['protein']}g, C:{macros['carbs']}g, F:{macros['fat']}g")
            if meal.get('notes'):
                click.echo(f"Notes: {meal['notes']}")
        
        click.echo("\n" + "=" * 80)
        click.echo(f"Total: {len(meals)} meal(s)")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        cleanup_services()


@cli.command()
@click.option('--id', 'meal_id', required=True, help='Meal ID')
@click.option('--name', help='Meal name')
@click.option('--calories', type=int, help='Total calories')
@click.option('--protein', type=float, help='Protein in grams')
@click.option('--carbs', type=float, help='Carbohydrates in grams')
@click.option('--fat', type=float, help='Fat in grams')
@click.option('--time', 'meal_time', help='Meal time (YYYY-MM-DD HH:MM)')
@click.option('--notes', help='Additional notes')
def update_meal(meal_id, name, calories, protein, carbs, fat, meal_time, notes):
    """Update an existing meal."""
    init_services()
    
    try:
        # Get meal
        meal = db_service.get_meal_by_id(meal_id)
        if not meal:
            click.echo(f"Error: Meal '{meal_id}' not found", err=True)
            sys.exit(1)
        
        # Prepare update data
        update_data = {}
        
        if name:
            update_data["name"] = name
        if calories:
            update_data["calories"] = calories
        
        # Handle macros
        if any([protein, carbs, fat]):
            macros = meal.get("macros", {})
            if protein is not None:
                macros["protein"] = protein
            if carbs is not None:
                macros["carbs"] = carbs
            if fat is not None:
                macros["fat"] = fat
            update_data["macros"] = macros
        
        if meal_time:
            try:
                update_data["time"] = datetime.strptime(meal_time, "%Y-%m-%d %H:%M")
            except ValueError:
                click.echo("Error: Invalid time format. Use YYYY-MM-DD HH:MM", err=True)
                sys.exit(1)
        
        if notes is not None:  # Allow empty string to clear notes
            update_data["notes"] = notes
        
        if not update_data:
            click.echo("Error: No fields to update", err=True)
            sys.exit(1)
        
        # Validate with Pydantic
        MealUpdate(**update_data)
        
        # Update meal
        success = db_service.update_meal(meal_id, update_data)
        
        if success:
            # Invalidate user's report cache
            report_service.invalidate_user_cache(meal["user_id"])
            click.echo("✅ Meal updated successfully!")
        else:
            click.echo("Error: Failed to update meal", err=True)
            sys.exit(1)
        
    except ValidationError as e:
        click.echo("Validation error:", err=True)
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            click.echo(f"  {field}: {error['msg']}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        cleanup_services()


@cli.command()
@click.option('--id', 'meal_id', required=True, help='Meal ID')
@click.confirmation_option(prompt='Are you sure you want to delete this meal?')
def delete_meal(meal_id):
    """Delete a meal."""
    init_services()
    
    try:
        # Get meal to get user_id for cache invalidation
        meal = db_service.get_meal_by_id(meal_id)
        if not meal:
            click.echo(f"Error: Meal '{meal_id}' not found", err=True)
            sys.exit(1)
        
        # Delete meal
        success = db_service.delete_meal(meal_id)
        
        if success:
            # Invalidate user's report cache
            report_service.invalidate_user_cache(meal["user_id"])
            click.echo("✅ Meal deleted successfully!")
        else:
            click.echo("Error: Failed to delete meal", err=True)
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        cleanup_services()


@cli.command()
@click.option('--user', required=True, help='Username')
@click.option('--weight', required=True, type=float, help='Weight in kilograms')
@click.option('--date', 'log_date', required=True, help='Date (YYYY-MM-DD)')
def log_weight(user, weight, log_date):
    """Log body weight."""
    init_services()
    
    try:
        # Get user
        user_doc = db_service.get_user_by_username(user)
        if not user_doc:
            click.echo(f"Error: User '{user}' not found", err=True)
            sys.exit(1)
        
        # Parse date
        try:
            log_date_obj = datetime.strptime(log_date, "%Y-%m-%d").date()
        except ValueError:
            click.echo("Error: Invalid date format. Use YYYY-MM-DD", err=True)
            sys.exit(1)
        
        # Prepare weight log data
        weight_data = {
            "user_id": user_doc["_id"],
            "weight_kg": weight,
            "date": log_date_obj
        }
        
        # Validate with Pydantic
        weight_log = WeightLogCreate(**weight_data)
        
        # Create weight log
        log_id = db_service.create_weight_log(weight_log.model_dump())
        
        # Invalidate user's report cache
        report_service.invalidate_user_cache(user_doc["_id"])
        
        click.echo(f"✅ Weight logged successfully!")
        click.echo(f"Log ID: {log_id}")
        
    except ValidationError as e:
        click.echo("Validation error:", err=True)
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            click.echo(f"  {field}: {error['msg']}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        cleanup_services()


@cli.command()
@click.option('--user', required=True, help='Username')
@click.option('--from', 'from_date', required=True, help='Start date (YYYY-MM-DD)')
@click.option('--to', 'to_date', required=True, help='End date (YYYY-MM-DD)')
@click.option('--no-cache', is_flag=True, help='Skip cache and regenerate report')
def view_report(user, from_date, to_date, no_cache):
    """View fitness progress report."""
    init_services()
    
    try:
        # Get user
        user_doc = db_service.get_user_by_username(user)
        if not user_doc:
            click.echo(f"Error: User '{user}' not found", err=True)
            sys.exit(1)
        
        # Parse dates
        try:
            start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
        except ValueError:
            click.echo("Error: Invalid date format. Use YYYY-MM-DD", err=True)
            sys.exit(1)
        
        if start_date > end_date:
            click.echo("Error: Start date must be before or equal to end date", err=True)
            sys.exit(1)
        
        # Generate report
        report = report_service.generate_report(
            user_doc["_id"],
            start_date,
            end_date,
            use_cache=not no_cache
        )
        
        # Display report
        click.echo("\n" + "=" * 80)
        click.echo(report["summary"])
        click.echo("=" * 80)
        
        if report.get("from_cache"):
            click.echo("\n💾 (Report loaded from cache)")
        
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        cleanup_services()


@cli.command()
@click.option('--user', required=True, help='Username')
@click.confirmation_option(prompt='Are you sure you want to delete this user and ALL associated data?')
def delete_user(user):
    """Delete a user and all associated data."""
    init_services()
    
    try:
        # Delete user
        success = db_service.delete_user(user)
        
        if success:
            # Try to invalidate cache (user_id may not be available)
            click.echo(f"✅ User '{user}' and all associated data deleted successfully!")
        else:
            click.echo(f"Error: User '{user}' not found", err=True)
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        cleanup_services()


if __name__ == '__main__':
    cli()
