import streamlit as st
from datetime import date, timedelta
from src.database import DatabaseManager
from src.services import get_workout_guidance


def render_daily_workout():
    """Render the daily workout view."""
    st.header("Today's Workout")

    db = DatabaseManager()

    # Date selector
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_date = st.date_input(
            "Select Date",
            value=date.today(),
            key="workout_date"
        )
    with col2:
        # Quick navigation
        if st.button("Today", use_container_width=True):
            st.session_state.workout_date = date.today()
            st.rerun()

    # Get programs for filtering
    programs = db.get_programs()

    if not programs:
        st.info("No workout programs found. Add a program first!")
        return

    # Program selector
    program_options = {p["name"]: p["id"] for p in programs}
    program_options["All Programs"] = None

    selected_program_name = st.selectbox(
        "Filter by Program",
        options=list(program_options.keys()),
        index=0
    )
    selected_program_id = program_options[selected_program_name]

    # Get workouts for selected date
    workouts = db.get_workouts_by_date_range(
        selected_date.isoformat(),
        selected_date.isoformat(),
        selected_program_id
    )

    if not workouts:
        st.warning(f"No workout scheduled for {selected_date.strftime('%A, %B %d, %Y')}")

        # Show upcoming workouts
        upcoming = db.get_workouts_by_date_range(
            selected_date.isoformat(),
            (selected_date + timedelta(days=7)).isoformat(),
            selected_program_id
        )

        if upcoming:
            st.subheader("Upcoming Workouts")
            for w in upcoming[:5]:
                with st.container():
                    st.write(f"**{w['scheduled_date']}** - {w['title'] or 'Workout'}")
        return

    # Display workout(s) for the day
    for workout in workouts:
        render_workout_card(workout, db)


def render_workout_card(workout: dict, db: DatabaseManager):
    """Render a single workout card."""
    workout_id = workout["id"]
    exercises = db.get_exercises_by_workout(workout_id)

    # Check if already completed
    existing_results = db.get_workout_results(workout_id)
    is_completed = len(existing_results) > 0

    # Workout header
    status_icon = "" if is_completed else ""
    st.subheader(f"{status_icon} {workout.get('title', 'Workout')}")

    # Workout meta
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Type:** {workout.get('workout_type', 'mixed').title()}")
    with col2:
        if workout.get("week_number"):
            st.write(f"**Week:** {workout['week_number']}")
    with col3:
        st.write(f"**Day:** {workout.get('day_number', 'N/A')}")

    if workout.get("description"):
        st.write(f"*{workout['description']}*")

    st.divider()

    # Get AI guidance
    if st.button("Get AI Guidance", key=f"guidance_{workout_id}"):
        with st.spinner("Getting personalized guidance..."):
            try:
                workout_data = {
                    "title": workout.get("title"),
                    "type": workout.get("workout_type"),
                    "exercises": [
                        {
                            "name": ex.get("exercise_name"),
                            "type": ex.get("exercise_type"),
                            "sets": ex.get("sets"),
                            "reps": ex.get("reps"),
                            "weight": ex.get("weight"),
                            "distance": ex.get("distance"),
                            "duration": ex.get("duration"),
                        }
                        for ex in exercises
                    ],
                }
                guidance = get_workout_guidance(workout_data)
                st.session_state[f"guidance_{workout_id}"] = guidance
            except Exception as e:
                st.error(f"Error getting guidance: {str(e)}")

    if f"guidance_{workout_id}" in st.session_state:
        with st.expander("AI Workout Guidance", expanded=True):
            st.markdown(st.session_state[f"guidance_{workout_id}"])

    # Exercise list
    st.subheader("Exercises")

    for i, exercise in enumerate(exercises):
        render_exercise_item(exercise, i, workout_id)

    # Start/Track workout button
    st.divider()

    if is_completed:
        st.success("Workout completed!")
        with st.expander("View Results"):
            result = existing_results[0]
            col1, col2 = st.columns(2)
            with col1:
                if result.get("total_duration_seconds"):
                    mins = result["total_duration_seconds"] // 60
                    secs = result["total_duration_seconds"] % 60
                    st.write(f"**Duration:** {mins}:{secs:02d}")
                if result.get("perceived_effort"):
                    st.write(f"**RPE:** {result['perceived_effort']}/10")
            with col2:
                if result.get("feeling"):
                    st.write(f"**Feeling:** {result['feeling'].title()}")
            if result.get("notes"):
                st.write(f"**Notes:** {result['notes']}")
    else:
        if st.button("Start Workout", key=f"start_{workout_id}", type="primary", use_container_width=True):
            st.session_state.active_workout = workout_id
            st.session_state.active_workout_exercises = exercises
            st.session_state.page = "track_workout"
            st.rerun()


def render_exercise_item(exercise: dict, index: int, workout_id: str):
    """Render a single exercise item."""
    with st.container():
        # Exercise name and type badge
        type_colors = {
            "run": "blue",
            "skierg": "orange",
            "sled_push": "red",
            "sled_pull": "red",
            "burpee_broad_jump": "violet",
            "rowing": "blue",
            "farmers_carry": "green",
            "sandbag_lunges": "green",
            "wall_balls": "orange",
            "strength": "gray",
            "cardio": "blue",
        }

        ex_type = exercise.get("exercise_type", "strength")
        color = type_colors.get(ex_type, "gray")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{index + 1}. {exercise.get('exercise_name')}**")
        with col2:
            st.caption(f":{color}[{ex_type.replace('_', ' ').title()}]")

        # Exercise details
        details = []
        if exercise.get("sets"):
            details.append(f"{exercise['sets']} sets")
        if exercise.get("reps"):
            details.append(f"{exercise['reps']} reps")
        if exercise.get("weight"):
            details.append(f"@ {exercise['weight']}")
        if exercise.get("distance"):
            details.append(exercise["distance"])
        if exercise.get("duration"):
            details.append(exercise["duration"])

        if details:
            st.write(" | ".join(details))

        if exercise.get("rest_period"):
            st.caption(f"Rest: {exercise['rest_period']}")

        if exercise.get("notes"):
            st.caption(f"*{exercise['notes']}*")

        st.write("")  # Spacing
