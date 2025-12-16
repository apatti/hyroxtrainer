import streamlit as st
from datetime import date, timedelta
from src.database import DatabaseManager
from src.services import parse_workout_program


def render_workout_input():
    """Render the workout input component."""
    st.header("Add Workout Program")

    with st.form("workout_input_form"):
        program_name = st.text_input(
            "Program Name",
            placeholder="e.g., 8-Week Hyrox Prep",
            help="Give your workout program a descriptive name"
        )

        start_date = st.date_input(
            "Start Date",
            value=date.today(),
            help="When does this program start?"
        )

        workout_text = st.text_area(
            "Workout Details",
            height=300,
            placeholder="""Paste your workout program here. Example:

Week 1:
Day 1 - Strength
- Squats: 4x8 @ RPE 7
- Romanian Deadlifts: 3x10
- Wall Balls: 3x20
- Core work: 3 rounds

Day 2 - Running
- 5km easy run
- 4x200m intervals with 90s rest

Day 3 - Hyrox Simulation
- 1km run
- 1000m SkiErg
- 1km run
- Sled Push 50m
...""",
            help="Describe your workouts in natural language - the AI will parse them"
        )

        submitted = st.form_submit_button("Parse & Save Workouts", use_container_width=True)

        if submitted:
            if not program_name or not workout_text:
                st.error("Please provide both a program name and workout details")
                return

            with st.spinner("Parsing workouts with AI..."):
                try:
                    # Parse workouts using LLM
                    parsed = parse_workout_program(
                        workout_text,
                        program_name,
                        start_date.isoformat()
                    )

                    # Store in session state for preview
                    st.session_state.parsed_workouts = parsed
                    st.session_state.raw_input = workout_text
                    st.session_state.program_name = program_name
                    st.session_state.start_date = start_date

                except Exception as e:
                    st.error(f"Error parsing workouts: {str(e)}")
                    return

    # Show preview if we have parsed workouts
    if "parsed_workouts" in st.session_state and st.session_state.parsed_workouts:
        render_workout_preview()


def render_workout_preview():
    """Render a preview of parsed workouts."""
    parsed = st.session_state.parsed_workouts

    st.subheader("Parsed Workout Preview")

    # Program info
    program = parsed.get("program", {})
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Program:** {program.get('name', 'Unknown')}")
        st.write(f"**Total Days:** {program.get('total_days', 'N/A')}")
    with col2:
        if program.get("total_weeks"):
            st.write(f"**Total Weeks:** {program.get('total_weeks')}")
        st.write(f"**Description:** {program.get('description', 'N/A')}")

    # Workouts
    workouts = parsed.get("workouts", [])

    for i, workout in enumerate(workouts):
        with st.expander(
            f"Day {workout.get('day_number', i+1)}: {workout.get('title', 'Workout')} "
            f"({workout.get('workout_type', 'mixed')})",
            expanded=i < 3  # Expand first 3
        ):
            if workout.get("scheduled_date"):
                st.write(f"**Date:** {workout.get('scheduled_date')}")
            if workout.get("description"):
                st.write(f"*{workout.get('description')}*")

            exercises = workout.get("exercises", [])
            for ex in exercises:
                exercise_str = f"**{ex.get('exercise_name')}**"

                details = []
                if ex.get("sets"):
                    details.append(f"{ex['sets']} sets")
                if ex.get("reps"):
                    details.append(f"{ex['reps']} reps")
                if ex.get("weight"):
                    details.append(f"@ {ex['weight']}")
                if ex.get("distance"):
                    details.append(ex["distance"])
                if ex.get("duration"):
                    details.append(ex["duration"])
                if ex.get("rest_period"):
                    details.append(f"(rest: {ex['rest_period']})")

                if details:
                    exercise_str += f" - {' '.join(details)}"

                if ex.get("notes"):
                    exercise_str += f"\n  *{ex['notes']}*"

                st.write(exercise_str)

    # Save button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save to Database", use_container_width=True, type="primary"):
            save_parsed_workouts()

    with col2:
        if st.button("Discard", use_container_width=True):
            clear_preview()


def save_parsed_workouts():
    """Save the parsed workouts to the database."""
    try:
        db = DatabaseManager()
        parsed = st.session_state.parsed_workouts
        program_info = parsed.get("program", {})

        # Create program
        program = db.create_program(
            name=program_info.get("name", st.session_state.program_name),
            description=program_info.get("description", ""),
            raw_input=st.session_state.raw_input,
            start_date=st.session_state.start_date.isoformat(),
        )

        if not program:
            st.error("Failed to create program")
            return

        program_id = program["id"]

        # Create workouts and exercises
        for workout_data in parsed.get("workouts", []):
            workout = db.create_workout(
                program_id=program_id,
                day_number=workout_data.get("day_number", 1),
                week_number=workout_data.get("week_number"),
                scheduled_date=workout_data.get("scheduled_date"),
                title=workout_data.get("title"),
                workout_type=workout_data.get("workout_type"),
                description=workout_data.get("description"),
            )

            if workout:
                # Create exercises
                exercises = []
                for ex in workout_data.get("exercises", []):
                    exercises.append({
                        "workout_id": workout["id"],
                        "exercise_order": ex.get("exercise_order", 1),
                        "exercise_name": ex.get("exercise_name"),
                        "exercise_type": ex.get("exercise_type"),
                        "sets": ex.get("sets"),
                        "reps": ex.get("reps"),
                        "weight": ex.get("weight"),
                        "distance": ex.get("distance"),
                        "duration": ex.get("duration"),
                        "rest_period": ex.get("rest_period"),
                        "notes": ex.get("notes"),
                    })

                if exercises:
                    db.create_exercises_batch(exercises)

        st.success(f"Successfully saved program '{program_info.get('name')}' with {len(parsed.get('workouts', []))} workouts!")
        clear_preview()
        st.rerun()

    except Exception as e:
        st.error(f"Error saving workouts: {str(e)}")


def clear_preview():
    """Clear the preview from session state."""
    for key in ["parsed_workouts", "raw_input", "program_name", "start_date"]:
        if key in st.session_state:
            del st.session_state[key]
