import streamlit as st
from datetime import datetime
from src.database import DatabaseManager


def render_workout_tracker():
    """Render the workout tracking interface."""
    st.header("Track Workout")

    if "active_workout" not in st.session_state:
        st.warning("No active workout. Go to Today's Workout to start one.")
        if st.button("Go to Today's Workout"):
            st.session_state.page = "today"
            st.rerun()
        return

    db = DatabaseManager()
    workout_id = st.session_state.active_workout
    workout = db.get_workout(workout_id)
    exercises = st.session_state.get("active_workout_exercises", [])

    if not workout:
        st.error("Workout not found")
        return

    # Workout header
    st.subheader(f"{workout.get('title', 'Workout')}")
    st.caption(f"Type: {workout.get('workout_type', 'mixed').title()}")

    # Initialize tracking state
    if "workout_start_time" not in st.session_state:
        st.session_state.workout_start_time = datetime.now()

    if "exercise_results" not in st.session_state:
        st.session_state.exercise_results = {}

    # Timer display
    elapsed = datetime.now() - st.session_state.workout_start_time
    elapsed_mins = int(elapsed.total_seconds() // 60)
    elapsed_secs = int(elapsed.total_seconds() % 60)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Elapsed Time", f"{elapsed_mins:02d}:{elapsed_secs:02d}")
    with col2:
        completed = sum(1 for ex in exercises if st.session_state.exercise_results.get(ex["id"], {}).get("completed", False))
        st.metric("Exercises", f"{completed}/{len(exercises)}")
    with col3:
        if st.button("Refresh Timer"):
            st.rerun()

    st.divider()

    # Exercise tracking
    st.subheader("Log Exercises")

    for i, exercise in enumerate(exercises):
        render_exercise_tracker(exercise, i)

    st.divider()

    # Workout completion
    st.subheader("Complete Workout")

    with st.form("complete_workout_form"):
        col1, col2 = st.columns(2)

        with col1:
            perceived_effort = st.slider(
                "RPE (Rate of Perceived Exertion)",
                min_value=1,
                max_value=10,
                value=7,
                help="1 = Very Easy, 10 = Maximum Effort"
            )

            feeling = st.selectbox(
                "How do you feel?",
                options=["great", "good", "okay", "tired", "exhausted"],
                index=1
            )

        with col2:
            heart_rate_avg = st.number_input(
                "Average Heart Rate (optional)",
                min_value=0,
                max_value=250,
                value=0,
                help="Leave at 0 if not tracking"
            )

            heart_rate_max = st.number_input(
                "Max Heart Rate (optional)",
                min_value=0,
                max_value=250,
                value=0
            )

        notes = st.text_area(
            "Workout Notes",
            placeholder="How did the workout go? Any observations?"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.form_submit_button("Complete Workout", type="primary", use_container_width=True):
                save_workout_results(
                    db,
                    workout_id,
                    exercises,
                    perceived_effort,
                    feeling,
                    heart_rate_avg if heart_rate_avg > 0 else None,
                    heart_rate_max if heart_rate_max > 0 else None,
                    notes
                )

        with col2:
            if st.form_submit_button("Cancel", use_container_width=True):
                clear_workout_state()
                st.session_state.page = "today"
                st.rerun()


def render_exercise_tracker(exercise: dict, index: int):
    """Render tracking interface for a single exercise."""
    exercise_id = exercise["id"]
    exercise_name = exercise.get("exercise_name", f"Exercise {index + 1}")

    # Initialize state for this exercise
    if exercise_id not in st.session_state.exercise_results:
        st.session_state.exercise_results[exercise_id] = {
            "completed": False,
            "sets_completed": exercise.get("sets", 1),
            "reps_completed": exercise.get("reps", ""),
            "weight_used": exercise.get("weight", ""),
            "time_seconds": None,
            "notes": "",
        }

    result = st.session_state.exercise_results[exercise_id]
    is_completed = result.get("completed", False)

    # Collapsible exercise section
    status_icon = "" if is_completed else ""

    with st.expander(f"{status_icon} {index + 1}. {exercise_name}", expanded=not is_completed):
        # Target values
        target_info = []
        if exercise.get("sets"):
            target_info.append(f"Sets: {exercise['sets']}")
        if exercise.get("reps"):
            target_info.append(f"Reps: {exercise['reps']}")
        if exercise.get("weight"):
            target_info.append(f"Weight: {exercise['weight']}")
        if exercise.get("distance"):
            target_info.append(f"Distance: {exercise['distance']}")
        if exercise.get("duration"):
            target_info.append(f"Duration: {exercise['duration']}")

        if target_info:
            st.caption(f"Target: {' | '.join(target_info)}")

        # Input fields based on exercise type
        col1, col2 = st.columns(2)

        with col1:
            if exercise.get("sets"):
                sets_completed = st.number_input(
                    "Sets Completed",
                    min_value=0,
                    max_value=20,
                    value=result.get("sets_completed") or exercise.get("sets", 1),
                    key=f"sets_{exercise_id}"
                )
                result["sets_completed"] = sets_completed

            reps_completed = st.text_input(
                "Reps Completed",
                value=result.get("reps_completed") or exercise.get("reps", ""),
                placeholder="e.g., 10,10,8 or 10",
                key=f"reps_{exercise_id}"
            )
            result["reps_completed"] = reps_completed

        with col2:
            if exercise.get("weight") or exercise.get("exercise_type") == "strength":
                weight_used = st.text_input(
                    "Weight Used",
                    value=result.get("weight_used") or exercise.get("weight", ""),
                    placeholder="e.g., 50kg",
                    key=f"weight_{exercise_id}"
                )
                result["weight_used"] = weight_used

            # Time input for cardio/timed exercises
            if exercise.get("duration") or exercise.get("distance") or \
               exercise.get("exercise_type") in ["run", "skierg", "rowing", "cardio"]:
                time_seconds = st.number_input(
                    "Time (seconds)",
                    min_value=0,
                    value=result.get("time_seconds") or 0,
                    key=f"time_{exercise_id}"
                )
                result["time_seconds"] = time_seconds if time_seconds > 0 else None

        # Notes
        exercise_notes = st.text_input(
            "Notes",
            value=result.get("notes", ""),
            placeholder="Any notes for this exercise?",
            key=f"notes_{exercise_id}"
        )
        result["notes"] = exercise_notes

        # Mark complete toggle
        completed = st.checkbox(
            "Mark as Complete",
            value=is_completed,
            key=f"complete_{exercise_id}"
        )
        result["completed"] = completed

        st.session_state.exercise_results[exercise_id] = result


def save_workout_results(db: DatabaseManager, workout_id: str, exercises: list,
                         perceived_effort: int, feeling: str,
                         heart_rate_avg: int, heart_rate_max: int, notes: str):
    """Save the workout results to the database."""
    try:
        # Calculate total duration
        elapsed = datetime.now() - st.session_state.workout_start_time
        total_duration = int(elapsed.total_seconds())

        # Create workout result
        workout_result = db.create_workout_result(
            workout_id=workout_id,
            total_duration_seconds=total_duration,
            perceived_effort=perceived_effort,
            heart_rate_avg=heart_rate_avg,
            heart_rate_max=heart_rate_max,
            notes=notes,
            feeling=feeling
        )

        if not workout_result:
            st.error("Failed to save workout result")
            return

        # Save exercise results
        exercise_results_to_save = []
        for exercise in exercises:
            ex_id = exercise["id"]
            result = st.session_state.exercise_results.get(ex_id, {})

            exercise_results_to_save.append({
                "workout_result_id": workout_result["id"],
                "workout_exercise_id": ex_id,
                "sets_completed": result.get("sets_completed"),
                "reps_completed": result.get("reps_completed"),
                "weight_used": result.get("weight_used"),
                "time_seconds": result.get("time_seconds"),
                "notes": result.get("notes"),
            })

        if exercise_results_to_save:
            db.create_exercise_results_batch(exercise_results_to_save)

        st.success("Workout completed and saved!")

        # Clear state and navigate
        clear_workout_state()
        st.session_state.page = "progress"
        st.rerun()

    except Exception as e:
        st.error(f"Error saving workout: {str(e)}")


def clear_workout_state():
    """Clear workout tracking state."""
    keys_to_remove = [
        "active_workout",
        "active_workout_exercises",
        "workout_start_time",
        "exercise_results",
    ]
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
