import os
import streamlit as st
from supabase import create_client, Client


def get_secret(key: str, default=None):
    """Get secret from Streamlit secrets (cloud) or environment (local)."""
    try:
        value = st.secrets.get(key)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(key, default)


def get_supabase_client() -> Client:
    """Get a Supabase client instance."""
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY must be set in secrets or environment variables"
        )

    return create_client(url, key)


class DatabaseManager:
    """Manager class for database operations."""

    def __init__(self):
        self.client = get_supabase_client()

    # Workout Programs
    def create_program(self, name: str, description: str, raw_input: str, start_date=None, end_date=None):
        """Create a new workout program."""
        data = {
            "name": name,
            "description": description,
            "raw_input": raw_input,
            "start_date": start_date,
            "end_date": end_date,
        }
        result = self.client.table("workout_programs").insert(data).execute()
        return result.data[0] if result.data else None

    def get_programs(self):
        """Get all workout programs."""
        result = self.client.table("workout_programs").select("*").order("created_at", desc=True).execute()
        return result.data

    def get_program(self, program_id: str):
        """Get a specific program by ID."""
        result = self.client.table("workout_programs").select("*").eq("id", program_id).execute()
        return result.data[0] if result.data else None

    def delete_program(self, program_id: str):
        """Delete a workout program."""
        result = self.client.table("workout_programs").delete().eq("id", program_id).execute()
        return result.data

    # Workouts
    def create_workout(self, program_id: str, day_number: int, week_number: int = None,
                       scheduled_date=None, title: str = None, workout_type: str = None,
                       description: str = None):
        """Create a new workout."""
        data = {
            "program_id": program_id,
            "day_number": day_number,
            "week_number": week_number,
            "scheduled_date": scheduled_date,
            "title": title,
            "workout_type": workout_type,
            "description": description,
        }
        result = self.client.table("workouts").insert(data).execute()
        return result.data[0] if result.data else None

    def get_workouts_by_program(self, program_id: str):
        """Get all workouts for a program."""
        result = (
            self.client.table("workouts")
            .select("*")
            .eq("program_id", program_id)
            .order("day_number")
            .execute()
        )
        return result.data

    def get_workout(self, workout_id: str):
        """Get a specific workout by ID."""
        result = self.client.table("workouts").select("*").eq("id", workout_id).execute()
        return result.data[0] if result.data else None

    def get_todays_workout(self, program_id: str = None):
        """Get today's scheduled workout."""
        from datetime import date
        today = date.today().isoformat()

        query = self.client.table("workouts").select("*").eq("scheduled_date", today)
        if program_id:
            query = query.eq("program_id", program_id)

        result = query.execute()
        return result.data

    def get_workouts_by_date_range(self, start_date: str, end_date: str, program_id: str = None):
        """Get workouts within a date range."""
        query = (
            self.client.table("workouts")
            .select("*")
            .gte("scheduled_date", start_date)
            .lte("scheduled_date", end_date)
        )
        if program_id:
            query = query.eq("program_id", program_id)

        result = query.order("scheduled_date").execute()
        return result.data

    # Workout Exercises
    def create_exercise(self, workout_id: str, exercise_order: int, exercise_name: str,
                        exercise_type: str = None, sets: int = None, reps: str = None,
                        weight: str = None, distance: str = None, duration: str = None,
                        rest_period: str = None, notes: str = None):
        """Create a new exercise."""
        data = {
            "workout_id": workout_id,
            "exercise_order": exercise_order,
            "exercise_name": exercise_name,
            "exercise_type": exercise_type,
            "sets": sets,
            "reps": reps,
            "weight": weight,
            "distance": distance,
            "duration": duration,
            "rest_period": rest_period,
            "notes": notes,
        }
        result = self.client.table("workout_exercises").insert(data).execute()
        return result.data[0] if result.data else None

    def create_exercises_batch(self, exercises: list):
        """Create multiple exercises at once."""
        result = self.client.table("workout_exercises").insert(exercises).execute()
        return result.data

    def get_exercises_by_workout(self, workout_id: str):
        """Get all exercises for a workout."""
        result = (
            self.client.table("workout_exercises")
            .select("*")
            .eq("workout_id", workout_id)
            .order("exercise_order")
            .execute()
        )
        return result.data

    # Workout Results
    def create_workout_result(self, workout_id: str, total_duration_seconds: int = None,
                              perceived_effort: int = None, heart_rate_avg: int = None,
                              heart_rate_max: int = None, notes: str = None, feeling: str = None):
        """Record a completed workout."""
        data = {
            "workout_id": workout_id,
            "total_duration_seconds": total_duration_seconds,
            "perceived_effort": perceived_effort,
            "heart_rate_avg": heart_rate_avg,
            "heart_rate_max": heart_rate_max,
            "notes": notes,
            "feeling": feeling,
        }
        result = self.client.table("workout_results").insert(data).execute()
        return result.data[0] if result.data else None

    def get_workout_results(self, workout_id: str = None, limit: int = 50):
        """Get workout results."""
        query = self.client.table("workout_results").select("*, workouts(*)")

        if workout_id:
            query = query.eq("workout_id", workout_id)

        result = query.order("completed_at", desc=True).limit(limit).execute()
        return result.data

    def get_all_results_with_details(self, limit: int = 100):
        """Get all workout results with workout details."""
        result = (
            self.client.table("workout_results")
            .select("*, workouts(*, workout_programs(*))")
            .order("completed_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data

    # Exercise Results
    def create_exercise_result(self, workout_result_id: str, workout_exercise_id: str,
                               sets_completed: int = None, reps_completed: str = None,
                               weight_used: str = None, time_seconds: int = None,
                               distance_completed: str = None, notes: str = None):
        """Record an individual exercise result."""
        data = {
            "workout_result_id": workout_result_id,
            "workout_exercise_id": workout_exercise_id,
            "sets_completed": sets_completed,
            "reps_completed": reps_completed,
            "weight_used": weight_used,
            "time_seconds": time_seconds,
            "distance_completed": distance_completed,
            "notes": notes,
        }
        result = self.client.table("exercise_results").insert(data).execute()
        return result.data[0] if result.data else None

    def create_exercise_results_batch(self, results: list):
        """Create multiple exercise results at once."""
        result = self.client.table("exercise_results").insert(results).execute()
        return result.data

    def get_exercise_results(self, workout_result_id: str):
        """Get exercise results for a workout result."""
        result = (
            self.client.table("exercise_results")
            .select("*, workout_exercises(*)")
            .eq("workout_result_id", workout_result_id)
            .execute()
        )
        return result.data

    # Personal Records
    def create_personal_record(self, exercise_type: str, exercise_name: str,
                               record_type: str, record_value: str,
                               workout_result_id: str = None, notes: str = None):
        """Create a new personal record."""
        data = {
            "exercise_type": exercise_type,
            "exercise_name": exercise_name,
            "record_type": record_type,
            "record_value": record_value,
            "workout_result_id": workout_result_id,
            "notes": notes,
        }
        result = self.client.table("personal_records").insert(data).execute()
        return result.data[0] if result.data else None

    def get_personal_records(self, exercise_type: str = None):
        """Get personal records."""
        query = self.client.table("personal_records").select("*")

        if exercise_type:
            query = query.eq("exercise_type", exercise_type)

        result = query.order("achieved_at", desc=True).execute()
        return result.data

    # Hyrox Race Results
    def create_race_result(self, race_date: str, total_time_seconds: int, **kwargs):
        """Record a Hyrox race result."""
        data = {
            "race_date": race_date,
            "total_time_seconds": total_time_seconds,
            **kwargs,
        }
        result = self.client.table("hyrox_race_results").insert(data).execute()
        return result.data[0] if result.data else None

    def get_race_results(self):
        """Get all race results."""
        result = (
            self.client.table("hyrox_race_results")
            .select("*")
            .order("race_date", desc=True)
            .execute()
        )
        return result.data

    # Analytics queries
    def get_workout_stats(self, days: int = 30):
        """Get workout statistics for the last N days."""
        from datetime import datetime, timedelta
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        result = (
            self.client.table("workout_results")
            .select("*")
            .gte("completed_at", start_date)
            .execute()
        )
        return result.data

    def get_exercise_history(self, exercise_name: str, limit: int = 20):
        """Get history for a specific exercise."""
        result = (
            self.client.table("exercise_results")
            .select("*, workout_exercises!inner(*), workout_results(*)")
            .ilike("workout_exercises.exercise_name", f"%{exercise_name}%")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data
