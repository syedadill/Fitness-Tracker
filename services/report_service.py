"""Report generation service with caching."""
from datetime import date, datetime
from typing import Dict, Any, Optional, List
from collections import Counter
from services.db_service import db_service
from services.cache_service import cache_service


class ReportService:
    """Service for generating fitness progress reports."""
    
    def __init__(self):
        """Initialize report service."""
        self.db = db_service
        self.cache = cache_service
    
    def generate_report(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive fitness report for a user.
        
        Args:
            user_id: User ID
            start_date: Report start date
            end_date: Report end date
            use_cache: Whether to use cached results
            
        Returns:
            Report dictionary with workout stats, nutrition, and weight trends
        """
        # Check cache first
        if use_cache:
            cache_key = self.cache.get_report_cache_key(
                user_id,
                start_date.isoformat(),
                end_date.isoformat()
            )
            cached = self.cache.get(cache_key)
            if cached:
                cached["from_cache"] = True
                return cached
        
        # Generate report
        report = self._build_report(user_id, start_date, end_date)
        report["from_cache"] = False
        
        # Cache the result
        if use_cache:
            cache_key = self.cache.get_report_cache_key(
                user_id,
                start_date.isoformat(),
                end_date.isoformat()
            )
            self.cache.set(cache_key, report)
        
        return report
    
    def _build_report(
        self,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Build the actual report data.
        
        Args:
            user_id: User ID or username
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Report dictionary
        """
        # Get user info - try by ID first, then by username
        user = self.db.get_user_by_id(user_id)
        if not user:
            user = self.db.get_user_by_username(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Use username for data queries (workouts, meals, weight_logs use user_id field which is username)
        username = user.get('username', user_id)
        
        # Fetch data
        workouts = self.db.get_workouts(username, start_date, end_date)
        meals = self.db.get_meals(username, start_date, end_date)
        weight_logs = self.db.get_weight_logs(username, start_date, end_date)
        
        # Calculate workout statistics
        workout_stats = self._calculate_workout_stats(workouts)
        
        # Calculate nutrition statistics
        nutrition_stats = self._calculate_nutrition_stats(meals, start_date, end_date)
        
        # Calculate weight trends
        weight_trends = self._calculate_weight_trends(weight_logs)
        
        # Generate summary
        summary = self._generate_summary(
            user,
            workout_stats,
            nutrition_stats,
            weight_trends,
            start_date,
            end_date
        )
        
        return {
            "user": {
                "username": user["username"],
                "email": user["email"],
                "full_name": user.get("full_name"),
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days + 1
            },
            "workouts": workout_stats,
            "nutrition": nutrition_stats,
            "weight": weight_trends,
            "summary": summary
        }
    
    def _calculate_workout_stats(self, workouts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate workout statistics."""
        if not workouts:
            return {
                "total_workouts": 0,
                "total_minutes": 0,
                "average_duration": 0,
                "intensity_breakdown": {"low": 0, "medium": 0, "high": 0},
                "workout_types": {}
            }
        
        total_minutes = sum(w["duration_minutes"] for w in workouts)
        intensity_counts = Counter(w["intensity"] for w in workouts)
        workout_types = Counter(w["type"] for w in workouts)
        
        return {
            "total_workouts": len(workouts),
            "total_minutes": total_minutes,
            "average_duration": round(total_minutes / len(workouts), 1),
            "intensity_breakdown": {
                "low": intensity_counts.get("low", 0),
                "medium": intensity_counts.get("medium", 0),
                "high": intensity_counts.get("high", 0)
            },
            "workout_types": dict(workout_types)
        }
    
    def _calculate_nutrition_stats(
        self,
        meals: List[Dict[str, Any]],
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Calculate nutrition statistics."""
        if not meals:
            return {
                "total_meals": 0,
                "total_calories": 0,
                "average_daily_calories": 0,
                "total_macros": {"protein": 0, "carbs": 0, "fat": 0},
                "average_daily_macros": {"protein": 0, "carbs": 0, "fat": 0}
            }
        
        total_calories = sum(m["calories"] for m in meals)
        total_protein = sum(m["macros"]["protein"] for m in meals)
        total_carbs = sum(m["macros"]["carbs"] for m in meals)
        total_fat = sum(m["macros"]["fat"] for m in meals)
        
        days = (end_date - start_date).days + 1
        
        return {
            "total_meals": len(meals),
            "total_calories": total_calories,
            "average_daily_calories": round(total_calories / days, 1),
            "total_macros": {
                "protein": round(total_protein, 1),
                "carbs": round(total_carbs, 1),
                "fat": round(total_fat, 1)
            },
            "average_daily_macros": {
                "protein": round(total_protein / days, 1),
                "carbs": round(total_carbs / days, 1),
                "fat": round(total_fat / days, 1)
            }
        }
    
    def _calculate_weight_trends(self, weight_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate weight trends."""
        if not weight_logs:
            return {
                "entries": 0,
                "start_weight": None,
                "end_weight": None,
                "change": None,
                "trend": "no data"
            }
        
        # Sort by date (oldest first)
        sorted_logs = sorted(
            weight_logs,
            key=lambda x: x["date"] if isinstance(x["date"], datetime) else datetime.combine(x["date"], datetime.min.time())
        )
        
        start_weight = sorted_logs[0]["weight_kg"]
        end_weight = sorted_logs[-1]["weight_kg"]
        change = round(end_weight - start_weight, 2)
        
        if change < 0:
            trend = "decreasing"
        elif change > 0:
            trend = "increasing"
        else:
            trend = "stable"
        
        return {
            "entries": len(weight_logs),
            "start_weight": round(start_weight, 2),
            "end_weight": round(end_weight, 2),
            "change": change,
            "trend": trend
        }
    
    def _generate_summary(
        self,
        user: Dict[str, Any],
        workout_stats: Dict[str, Any],
        nutrition_stats: Dict[str, Any],
        weight_trends: Dict[str, Any],
        start_date: date,
        end_date: date
    ) -> str:
        """Generate a human-readable summary."""
        days = (end_date - start_date).days + 1
        lines = []
        
        lines.append(f"Fitness Report for {user['username']} ({start_date} to {end_date})")
        lines.append(f"Period: {days} days")
        lines.append("")
        
        # Workout summary
        if workout_stats["total_workouts"] > 0:
            lines.append(f"🏋️ Workouts: {workout_stats['total_workouts']} sessions, "
                        f"{workout_stats['total_minutes']} total minutes")
            lines.append(f"   Average duration: {workout_stats['average_duration']} minutes")
            
            intensity = workout_stats['intensity_breakdown']
            lines.append(f"   Intensity: {intensity['low']} low, {intensity['medium']} medium, "
                        f"{intensity['high']} high")
        else:
            lines.append("🏋️ No workouts logged in this period")
        
        lines.append("")
        
        # Nutrition summary
        if nutrition_stats["total_meals"] > 0:
            lines.append(f"🍽️ Nutrition: {nutrition_stats['total_meals']} meals logged")
            lines.append(f"   Average daily calories: {nutrition_stats['average_daily_calories']}")
            macros = nutrition_stats['average_daily_macros']
            lines.append(f"   Average daily macros: P:{macros['protein']}g, "
                        f"C:{macros['carbs']}g, F:{macros['fat']}g")
        else:
            lines.append("🍽️ No meals logged in this period")
        
        lines.append("")
        
        # Weight summary
        if weight_trends["entries"] > 0:
            lines.append(f"⚖️ Weight: {weight_trends['entries']} measurements")
            lines.append(f"   Start: {weight_trends['start_weight']} kg")
            lines.append(f"   End: {weight_trends['end_weight']} kg")
            change = weight_trends['change']
            change_str = f"+{change}" if change > 0 else str(change)
            lines.append(f"   Change: {change_str} kg ({weight_trends['trend']})")
            
            # Compare with goal if available
            goals = user.get("goals", {})
            target_weight = goals.get("target_weight") if goals else None
            if target_weight:
                diff = round(weight_trends['end_weight'] - target_weight, 2)
                if diff > 0:
                    lines.append(f"   Target: {target_weight} kg ({diff} kg above target)")
                elif diff < 0:
                    lines.append(f"   Target: {target_weight} kg ({abs(diff)} kg below target)")
                else:
                    lines.append(f"   Target: {target_weight} kg (target reached!)")
        else:
            lines.append("⚖️ No weight measurements in this period")
        
        # Goals comparison
        goals = user.get("goals", {})
        if goals:
            weekly_goal = goals.get("weekly_workout_minutes")
            if weekly_goal and workout_stats["total_workouts"] > 0:
                weeks = days / 7
                actual_weekly = workout_stats["total_minutes"] / weeks
                lines.append("")
                lines.append(f"📊 Weekly workout goal: {weekly_goal} minutes")
                lines.append(f"   Actual average: {round(actual_weekly, 1)} minutes/week")
                if actual_weekly >= weekly_goal:
                    lines.append("   ✅ Goal achieved!")
                else:
                    deficit = round(weekly_goal - actual_weekly, 1)
                    lines.append(f"   ⚠️ {deficit} minutes short of weekly goal")
        
        return "\n".join(lines)
    
    def invalidate_user_cache(self, user_id: str) -> int:
        """
        Invalidate all cached reports for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of cache entries invalidated
        """
        return self.cache.invalidate_user_reports(user_id)


# Global report service instance
report_service = ReportService()
