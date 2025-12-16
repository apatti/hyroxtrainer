import streamlit as st
from datetime import datetime
from src.database import DatabaseManager
from src.services import get_coaching_insights, analyze_race_performance


def render_coaching():
    """Render the AI coaching interface."""
    st.header("AI Coach")

    db = DatabaseManager()

    # Tabs for different coaching features
    tab1, tab2, tab3 = st.tabs(["Ask Coach", "Race Analysis", "Training Plan Review"])

    with tab1:
        render_ask_coach(db)

    with tab2:
        render_race_analysis(db)

    with tab3:
        render_training_review(db)


def render_ask_coach(db: DatabaseManager):
    """Render the ask coach chat interface."""
    st.subheader("Ask Your AI Coach")

    # Initialize chat history
    if "coach_messages" not in st.session_state:
        st.session_state.coach_messages = []

    # Display chat history
    for message in st.session_state.coach_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask your coach anything about Hyrox training..."):
        # Add user message
        st.session_state.coach_messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Gather context
                    workout_stats = db.get_workout_stats(30)
                    personal_records = db.get_personal_records()

                    performance_data = {
                        "recent_workouts": len(workout_stats),
                        "personal_records": [
                            {"exercise": pr.get("exercise_name"), "value": pr.get("record_value")}
                            for pr in personal_records[:5]
                        ],
                        "recent_performance": [
                            {
                                "rpe": w.get("perceived_effort"),
                                "feeling": w.get("feeling"),
                                "duration_mins": (w.get("total_duration_seconds") or 0) / 60,
                            }
                            for w in workout_stats[-5:]
                        ]
                    }

                    response = get_coaching_insights(performance_data, question=prompt)
                    st.markdown(response)

                    st.session_state.coach_messages.append({
                        "role": "assistant",
                        "content": response
                    })

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)

    # Quick question buttons
    st.divider()
    st.caption("Quick Questions:")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("How should I improve my SkiErg?", use_container_width=True):
            st.session_state.coach_messages.append({
                "role": "user",
                "content": "How should I improve my SkiErg performance for Hyrox?"
            })
            st.rerun()

        if st.button("What's a good race day strategy?", use_container_width=True):
            st.session_state.coach_messages.append({
                "role": "user",
                "content": "What's a good race day strategy for my first Hyrox?"
            })
            st.rerun()

    with col2:
        if st.button("Am I training enough?", use_container_width=True):
            st.session_state.coach_messages.append({
                "role": "user",
                "content": "Based on my training data, am I training enough to be competitive?"
            })
            st.rerun()

        if st.button("Where are my weaknesses?", use_container_width=True):
            st.session_state.coach_messages.append({
                "role": "user",
                "content": "Based on my performance data, what are my biggest weaknesses I should focus on?"
            })
            st.rerun()

    # Clear chat button
    if st.session_state.coach_messages:
        if st.button("Clear Chat"):
            st.session_state.coach_messages = []
            st.rerun()


def render_race_analysis(db: DatabaseManager):
    """Render race result analysis."""
    st.subheader("Hyrox Race Analysis")

    # Get existing race results
    race_results = db.get_race_results()

    if race_results:
        st.write("**Your Race History:**")
        for race in race_results:
            total_mins = (race.get("total_time_seconds") or 0) // 60
            total_secs = (race.get("total_time_seconds") or 0) % 60
            race_date = race.get("race_date", "Unknown")

            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{race.get('race_location', 'Unknown Location')}**")
            with col2:
                st.write(race_date)
            with col3:
                st.write(f"{total_mins}:{total_secs:02d}")

            if st.button(f"Analyze", key=f"analyze_{race['id']}"):
                with st.spinner("Analyzing race performance..."):
                    try:
                        training_history = db.get_workout_stats(90)
                        analysis = analyze_race_performance(race, {"workouts": len(training_history)})
                        st.markdown(analysis)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        st.divider()

    # Add new race result
    st.subheader("Add Race Result")

    with st.form("race_result_form"):
        col1, col2 = st.columns(2)

        with col1:
            race_date = st.date_input("Race Date")
            race_location = st.text_input("Location", placeholder="e.g., London Excel")
            division = st.selectbox("Division", ["open", "pro", "doubles"])

        with col2:
            total_mins = st.number_input("Total Time (minutes)", min_value=0, value=60)
            total_secs = st.number_input("Total Time (seconds)", min_value=0, max_value=59, value=0)

        st.write("**Station Times (optional - in seconds):**")

        # Station times in a grid
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            skierg = st.number_input("SkiErg", min_value=0, value=0)
            sled_push = st.number_input("Sled Push", min_value=0, value=0)
            rowing = st.number_input("Rowing", min_value=0, value=0)
            wall_balls = st.number_input("Wall Balls", min_value=0, value=0)

        with col2:
            sled_pull = st.number_input("Sled Pull", min_value=0, value=0)
            burpee_bj = st.number_input("Burpee Broad Jump", min_value=0, value=0)
            farmers = st.number_input("Farmers Carry", min_value=0, value=0)
            lunges = st.number_input("Sandbag Lunges", min_value=0, value=0)

        with col3:
            run_1 = st.number_input("Run 1", min_value=0, value=0)
            run_2 = st.number_input("Run 2", min_value=0, value=0)
            run_3 = st.number_input("Run 3", min_value=0, value=0)
            run_4 = st.number_input("Run 4", min_value=0, value=0)

        with col4:
            run_5 = st.number_input("Run 5", min_value=0, value=0)
            run_6 = st.number_input("Run 6", min_value=0, value=0)
            run_7 = st.number_input("Run 7", min_value=0, value=0)
            run_8 = st.number_input("Run 8", min_value=0, value=0)

        transitions = st.number_input("Total Transition Time", min_value=0, value=0)
        notes = st.text_area("Race Notes")

        if st.form_submit_button("Save Race Result"):
            total_time_seconds = total_mins * 60 + total_secs

            try:
                db.create_race_result(
                    race_date=race_date.isoformat(),
                    total_time_seconds=total_time_seconds,
                    race_location=race_location,
                    division=division,
                    skierg_time=skierg if skierg > 0 else None,
                    sled_push_time=sled_push if sled_push > 0 else None,
                    sled_pull_time=sled_pull if sled_pull > 0 else None,
                    burpee_broad_jump_time=burpee_bj if burpee_bj > 0 else None,
                    rowing_time=rowing if rowing > 0 else None,
                    farmers_carry_time=farmers if farmers > 0 else None,
                    sandbag_lunges_time=lunges if lunges > 0 else None,
                    wall_balls_time=wall_balls if wall_balls > 0 else None,
                    run_1_time=run_1 if run_1 > 0 else None,
                    run_2_time=run_2 if run_2 > 0 else None,
                    run_3_time=run_3 if run_3 > 0 else None,
                    run_4_time=run_4 if run_4 > 0 else None,
                    run_5_time=run_5 if run_5 > 0 else None,
                    run_6_time=run_6 if run_6 > 0 else None,
                    run_7_time=run_7 if run_7 > 0 else None,
                    run_8_time=run_8 if run_8 > 0 else None,
                    transitions_total_time=transitions if transitions > 0 else None,
                    notes=notes,
                )
                st.success("Race result saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving race result: {str(e)}")


def render_training_review(db: DatabaseManager):
    """Render training plan review."""
    st.subheader("Training Plan Review")

    programs = db.get_programs()

    if not programs:
        st.info("No training programs found. Add a program first!")
        return

    # Select program to review
    program_options = {p["name"]: p["id"] for p in programs}
    selected_program_name = st.selectbox(
        "Select Program",
        options=list(program_options.keys())
    )
    selected_program_id = program_options[selected_program_name]

    # Get program details
    program = db.get_program(selected_program_id)
    workouts = db.get_workouts_by_program(selected_program_id)

    if not workouts:
        st.warning("No workouts found for this program.")
        return

    # Display program info
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Total Workouts:** {len(workouts)}")
    with col2:
        if program.get("start_date"):
            st.write(f"**Start Date:** {program['start_date']}")

    # Get AI review
    if st.button("Get AI Training Plan Review"):
        with st.spinner("Analyzing your training plan..."):
            try:
                # Prepare workout summary for analysis
                workout_summary = []
                for w in workouts[:20]:  # First 20 workouts
                    exercises = db.get_exercises_by_workout(w["id"])
                    workout_summary.append({
                        "day": w.get("day_number"),
                        "type": w.get("workout_type"),
                        "title": w.get("title"),
                        "exercise_count": len(exercises),
                        "exercises": [ex.get("exercise_name") for ex in exercises],
                    })

                performance_data = {
                    "program_name": selected_program_name,
                    "total_workouts": len(workouts),
                    "workout_types": list(set(w.get("workout_type") for w in workouts if w.get("workout_type"))),
                    "sample_workouts": workout_summary,
                }

                review = get_coaching_insights(
                    performance_data,
                    question="Please review this Hyrox training program and provide feedback on its structure, balance, and effectiveness for race preparation."
                )
                st.markdown(review)

            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Workout type distribution
    st.divider()
    st.write("**Workout Distribution:**")

    workout_types = {}
    for w in workouts:
        wtype = w.get("workout_type", "unknown")
        workout_types[wtype] = workout_types.get(wtype, 0) + 1

    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    for i, (wtype, count) in enumerate(workout_types.items()):
        with cols[i % 4]:
            st.metric(wtype.title(), count)
