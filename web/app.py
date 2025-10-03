"""
Flask web application for Fitness Tracker.
Provides REST API endpoints for the web interface.
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from datetime import datetime, date
from typing import Optional
import sys
import os

# Add parent directory to path to import project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import global service instances
from services.db_service import db_service
from services.cache_service import cache_service
from services.report_service import report_service
from models.schemas import (
    UserCreate, WorkoutCreate, WorkoutUpdate,
    MealCreate, MealUpdate, WeightLogCreate
)
from pydantic import ValidationError

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Connect to services on startup
try:
    db_service.connect()
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    print("⚠️  Application will not work without database connection")


@app.route('/')
def index():
    """Serve the main web interface."""
    return render_template('index.html')


# ============================================================================
# User Endpoints
# ============================================================================

@app.route('/api/users', methods=['POST'])
def register_user():
    """Register a new user."""
    try:
        data = request.json
        user_data = UserCreate(**data)
        # Convert Pydantic model to dict, excluding None values
        user_dict = user_data.model_dump(exclude_none=True)
        user_id = db_service.create_user(user_dict)
        return jsonify({'success': True, 'user_id': user_id, 'message': 'User registered successfully'}), 201
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/users/<username>', methods=['GET'])
def get_user(username: str):
    """Get user information."""
    try:
        user = db_service.get_user_by_username(username)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Convert ObjectId to string and date to ISO format
        user['_id'] = str(user['_id'])
        if 'created_at' in user:
            user['created_at'] = user['created_at'].isoformat()
        
        return jsonify({'success': True, 'user': user}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/users/<username>', methods=['DELETE'])
def delete_user(username: str):
    """Delete a user and all associated data."""
    try:
        success = db_service.delete_user(username)
        if success:
            # Invalidate cached reports
            cache_service.invalidate_user_reports(username)
            return jsonify({'success': True, 'message': 'User deleted successfully'}), 200
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# Workout Endpoints
# ============================================================================

@app.route('/api/workouts', methods=['POST'])
def add_workout():
    """Add a new workout."""
    try:
        data = request.json
        workout_data = WorkoutCreate(**data)
        # Convert Pydantic model to dict
        workout_dict = workout_data.model_dump(exclude_none=True)
        workout_id = db_service.create_workout(workout_dict)
        
        # Invalidate cached reports
        cache_service.invalidate_user_reports(workout_data.user_id)
        
        return jsonify({'success': True, 'workout_id': workout_id, 'message': 'Workout added successfully'}), 201
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/workouts/<username>', methods=['GET'])
def get_workouts(username: str):
    """Get workouts for a user."""
    try:
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        # Convert string dates to date objects
        from_date_obj = datetime.fromisoformat(from_date).date() if from_date else None
        to_date_obj = datetime.fromisoformat(to_date).date() if to_date else None
        
        workouts = db_service.get_workouts(username, from_date_obj, to_date_obj)
        
        # Convert ObjectId and dates to strings
        for workout in workouts:
            workout['_id'] = str(workout['_id'])
            if 'date' in workout:
                workout['date'] = workout['date'].isoformat()
            if 'created_at' in workout:
                workout['created_at'] = workout['created_at'].isoformat()
        
        return jsonify({'success': True, 'workouts': workouts}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/workouts/<workout_id>', methods=['PUT'])
def update_workout(workout_id: str):
    """Update a workout."""
    try:
        data = request.json
        workout_update = WorkoutUpdate(**data)
        # Convert Pydantic model to dict
        workout_dict = workout_update.model_dump(exclude_none=True)
        success = db_service.update_workout(workout_id, workout_dict)
        
        if success:
            # Get workout to invalidate cache for the right user
            workout = db_service.get_workout_by_id(workout_id)
            if workout:
                cache_service.invalidate_user_reports(workout['user_id'])
            
            return jsonify({'success': True, 'message': 'Workout updated successfully'}), 200
        else:
            return jsonify({'success': False, 'error': 'Workout not found'}), 404
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/workouts/<workout_id>', methods=['DELETE'])
def delete_workout(workout_id: str):
    """Delete a workout."""
    try:
        # Get workout to invalidate cache for the right user
        workout = db_service.get_workout_by_id(workout_id)
        
        success = db_service.delete_workout(workout_id)
        
        if success:
            if workout:
                cache_service.invalidate_user_reports(workout['user_id'])
            return jsonify({'success': True, 'message': 'Workout deleted successfully'}), 200
        else:
            return jsonify({'success': False, 'error': 'Workout not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# Meal Endpoints
# ============================================================================

@app.route('/api/meals', methods=['POST'])
def add_meal():
    """Add a new meal."""
    try:
        data = request.json
        meal_data = MealCreate(**data)
        # Convert Pydantic model to dict
        meal_dict = meal_data.model_dump(exclude_none=True)
        meal_id = db_service.create_meal(meal_dict)
        
        # Invalidate cached reports
        cache_service.invalidate_user_reports(meal_data.user_id)
        
        return jsonify({'success': True, 'meal_id': meal_id, 'message': 'Meal added successfully'}), 201
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/meals/<username>', methods=['GET'])
def get_meals(username: str):
    """Get meals for a user."""
    try:
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        # Convert string dates to date objects
        from_date_obj = datetime.fromisoformat(from_date).date() if from_date else None
        to_date_obj = datetime.fromisoformat(to_date).date() if to_date else None
        
        meals = db_service.get_meals(username, from_date_obj, to_date_obj)
        
        # Convert ObjectId and dates to strings
        for meal in meals:
            meal['_id'] = str(meal['_id'])
            if 'time' in meal:
                meal['time'] = meal['time'].isoformat()
            if 'created_at' in meal:
                meal['created_at'] = meal['created_at'].isoformat()
        
        return jsonify({'success': True, 'meals': meals}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/meals/<meal_id>', methods=['PUT'])
def update_meal(meal_id: str):
    """Update a meal."""
    try:
        data = request.json
        meal_update = MealUpdate(**data)
        # Convert Pydantic model to dict
        meal_dict = meal_update.model_dump(exclude_none=True)
        success = db_service.update_meal(meal_id, meal_dict)
        
        if success:
            # Get meal to invalidate cache for the right user
            meal = db_service.get_meal_by_id(meal_id)
            if meal:
                cache_service.invalidate_user_reports(meal['user_id'])
            
            return jsonify({'success': True, 'message': 'Meal updated successfully'}), 200
        else:
            return jsonify({'success': False, 'error': 'Meal not found'}), 404
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/meals/<meal_id>', methods=['DELETE'])
def delete_meal(meal_id: str):
    """Delete a meal."""
    try:
        # Get meal to invalidate cache for the right user
        meal = db_service.get_meal_by_id(meal_id)
        
        success = db_service.delete_meal(meal_id)
        
        if success:
            if meal:
                cache_service.invalidate_user_reports(meal['user_id'])
            return jsonify({'success': True, 'message': 'Meal deleted successfully'}), 200
        else:
            return jsonify({'success': False, 'error': 'Meal not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# Weight Log Endpoints
# ============================================================================

@app.route('/api/weight-logs', methods=['POST'])
def add_weight_log():
    """Add a new weight log."""
    try:
        data = request.json
        weight_data = WeightLogCreate(**data)
        # Convert Pydantic model to dict
        weight_dict = weight_data.model_dump(exclude_none=True)
        log_id = db_service.create_weight_log(weight_dict)
        
        # Invalidate cached reports
        cache_service.invalidate_user_reports(weight_data.user_id)
        
        return jsonify({'success': True, 'log_id': log_id, 'message': 'Weight logged successfully'}), 201
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/weight-logs/<username>', methods=['GET'])
def get_weight_logs(username: str):
    """Get weight logs for a user."""
    try:
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        # Convert string dates to date objects
        from_date_obj = datetime.fromisoformat(from_date).date() if from_date else None
        to_date_obj = datetime.fromisoformat(to_date).date() if to_date else None
        
        logs = db_service.get_weight_logs(username, from_date_obj, to_date_obj)
        
        # Convert ObjectId and dates to strings
        for log in logs:
            log['_id'] = str(log['_id'])
            if 'date' in log:
                log['date'] = log['date'].isoformat()
            if 'created_at' in log:
                log['created_at'] = log['created_at'].isoformat()
        
        return jsonify({'success': True, 'logs': logs}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/weight-logs/<log_id>', methods=['DELETE'])
def delete_weight_log(log_id: str):
    """Delete a weight log."""
    try:
        # Get log to invalidate cache for the right user
        log = db_service.get_weight_log_by_id(log_id)
        
        success = db_service.delete_weight_log(log_id)
        
        if success:
            if log:
                cache_service.invalidate_user_reports(log['user_id'])
            return jsonify({'success': True, 'message': 'Weight log deleted successfully'}), 200
        else:
            return jsonify({'success': False, 'error': 'Weight log not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# Report Endpoints
# ============================================================================

@app.route('/api/reports/<username>', methods=['GET'])
def get_report(username: str):
    """Generate and get a fitness report for a user."""
    try:
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        no_cache = request.args.get('no_cache', 'false').lower() == 'true'
        
        if not from_date or not to_date:
            return jsonify({'success': False, 'error': 'from_date and to_date are required'}), 400
        
        # Convert string dates to date objects
        from_date_obj = datetime.fromisoformat(from_date).date()
        to_date_obj = datetime.fromisoformat(to_date).date()
        
        report = report_service.generate_report(
            username, from_date_obj, to_date_obj, use_cache=not no_cache
        )
        
        if not report:
            return jsonify({'success': False, 'error': 'User not found or no data available'}), 404
        
        return jsonify({'success': True, 'report': report}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# Health Check
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if the API is running and services are connected."""
    try:
        # Check MongoDB connection
        db_connected = db_service.client.admin.command('ping')['ok'] == 1
        
        # Check Redis connection
        redis_connected = cache_service.is_available()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'services': {
                'database': 'connected' if db_connected else 'disconnected',
                'cache': 'connected' if redis_connected else 'disconnected'
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
