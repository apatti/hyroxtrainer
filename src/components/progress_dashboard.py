import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from src.database import DatabaseManager
from src.services import get_coaching_insights


def render_progress_dashboard():
    """Render the progress dashboard."""
    st.header("Progress Dashboard")

    db = DatabaseManager()

    # Time range selector
    col1, col2 = st.columns([2, 1])
    with col1:
        time_range = st.selectbox(
            "Time Range",
            options=["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
            index=1
        )
    with col2:
        if st.button("Get AI Analysis", use_container_width=True):
            st.session_state.show_ai_analysis = True

    # Calculate date range
    days_map = {
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90,
        "All time": 365 * 10,
    }
    days = days_map[time_range]

    # Get workout stats
    workout_results = db.get_workout_stats(days)

    if not workout_results:
        st.info("No workout data found. Complete some workouts to see your progress!")
        return

    # Summary metrics
    render_summary_metrics(workout_results)

    st.divider()

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Workout History", "Volume Trends", "Performance", "Personal Records"])

    with tab1:
        render_workout_history(workout_results, db)

    with tab2:
        render_volume_trends(workout_results)

    with tab3:
        render_performance_charts(workout_results, db)

    with tab4:
        render_personal_records(db)

    # AI Analysis section
    if st.session_state.get("show_ai_analysis"):
        render_ai_analysis(workout_results, db)


def render_summary_metrics(workout_results: list):
    """Render summary metrics cards."""
    col1, col2, col3, col4 = st.columns(4)

    total_workouts = len(workout_results)

    # Calculate total time
    total_time_seconds = sum(r.get("total_duration_seconds", 0) or 0 for r in workout_results)
    total_hours = total_time_seconds / 3600

    # Average RPE
    rpe_values = [r.get("perceived_effort") for r in workout_results if r.get("perceived_effort")]
    avg_rpe = sum(rpe_values) / len(rpe_values) if rpe_values else 0

    # Workout streak (consecutive days)
    dates = sorted(set(
        datetime.fromisoformat(r["completed_at"].replace("Z", "+00:00")).date()
        for r in workout_results if r.get("completed_at")
    ))
    streak = calculate_streak(dates)

    with col1:
        st.metric("Total Workouts", total_workouts)
    with col2:
        st.metric("Total Time", f"{total_hours:.1f} hrs")
    with col3:
        st.metric("Avg RPE", f"{avg_rpe:.1f}/10")
    with col4:
        st.metric("Current Streak", f"{streak} days")


def calculate_streak(dates: list) -> int:
    """Calculate current workout streak."""
    if not dates:
        return 0

    from datetime import date
    today = date.today()
    yesterday = today - timedelta(days=1)

    # Check if worked out today or yesterday
    if dates[-1] != today and dates[-1] != yesterday:
        return 0

    streak = 1
    for i in range(len(dates) - 1, 0, -1):
        if (dates[i] - dates[i-1]).days == 1:
            streak += 1
        else:
            break

    return streak


def render_workout_history(workout_results: list, db: DatabaseManager):
    """Render workout history list."""
    st.subheader("Recent Workouts")

    # Get results with workout details
    detailed_results = db.get_all_results_with_details(limit=50)

    if not detailed_results:
        st.info("No workout history yet.")
        return

    for result in detailed_results[:20]:
        workout = result.get("workouts", {})
        program = workout.get("workout_programs", {}) if workout else {}

        completed_at = result.get("completed_at", "")
        if completed_at:
            dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%b %d, %Y %I:%M %p")
        else:
            date_str = "Unknown"

        # Duration
        duration_secs = result.get("total_duration_seconds", 0) or 0
        duration_str = f"{duration_secs // 60}:{duration_secs % 60:02d}"

        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                workout_title = workout.get("title", "Workout") if workout else "Workout"
                program_name = program.get("name", "") if program else ""
                st.write(f"**{workout_title}**")
                if program_name:
                    st.caption(program_name)

            with col2:
                st.write(f"{date_str}")

            with col3:
                feeling = result.get("feeling", "")
                feeling_emoji = {
                    "great": "",
                    "good": "",
                    "okay": "",
                    "tired": "",
                    "exhausted": "",
                }.get(feeling, "")

                st.write(f"{duration_str} | RPE {result.get('perceived_effort', 'N/A')} {feeling_emoji}")

            if result.get("notes"):
                st.caption(f"*{result['notes']}*")

            st.divider()


def render_volume_trends(workout_results: list):
    """Render volume/frequency trends."""
    st.subheader("Training Volume")

    if not workout_results:
        return

    # Prepare data
    df = pd.DataFrame(workout_results)
    df["completed_at"] = pd.to_datetime(df["completed_at"])
    df["date"] = df["completed_at"].dt.date
    df["week"] = df["completed_at"].dt.isocalendar().week

    # Workouts per week
    weekly_counts = df.groupby("week").size().reset_index(name="workouts")

    fig = px.bar(
        weekly_counts,
        x="week",
        y="workouts",
        title="Workouts per Week",
        labels={"week": "Week Number", "workouts": "Number of Workouts"},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Training time trend
    df["duration_mins"] = df["total_duration_seconds"].fillna(0) / 60
    daily_duration = df.groupby("date")["duration_mins"].sum().reset_index()

    fig2 = px.area(
        daily_duration,
        x="date",
        y="duration_mins",
        title="Daily Training Time",
        labels={"date": "Date", "duration_mins": "Minutes"},
    )
    st.plotly_chart(fig2, use_container_width=True)


def render_performance_charts(workout_results: list, db: DatabaseManager):
    """Render performance-related charts."""
    st.subheader("Performance Metrics")

    if not workout_results:
        return

    df = pd.DataFrame(workout_results)
    df["completed_at"] = pd.to_datetime(df["completed_at"])

    # RPE trend
    if df["perceived_effort"].notna().any():
        fig = px.line(
            df.sort_values("completed_at"),
            x="completed_at",
            y="perceived_effort",
            title="Perceived Effort Over Time",
            labels={"completed_at": "Date", "perceived_effort": "RPE (1-10)"},
            markers=True,
        )
        fig.update_layout(yaxis_range=[0, 10])
        st.plotly_chart(fig, use_container_width=True)

    # Feeling distribution
    feeling_counts = df["feeling"].value_counts()
    if not feeling_counts.empty:
        col1, col2 = st.columns(2)

        with col1:
            fig2 = px.pie(
                values=feeling_counts.values,
                names=feeling_counts.index,
                title="Post-Workout Feelings",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            # Heart rate distribution if available
            hr_data = df[df["heart_rate_avg"].notna()]
            if not hr_data.empty:
                fig3 = px.scatter(
                    hr_data,
                    x="perceived_effort",
                    y="heart_rate_avg",
                    title="RPE vs Avg Heart Rate",
                    labels={"perceived_effort": "RPE", "heart_rate_avg": "Avg HR"},
                    trendline="ols",
                )
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("No heart rate data available yet.")


def render_personal_records(db: DatabaseManager):
    """Render personal records section."""
    st.subheader("Personal Records")

    records = db.get_personal_records()

    if not records:
        st.info("No personal records yet. Keep training!")

        # Show button to add PR manually
        with st.expander("Add Personal Record"):
            render_add_pr_form(db)
        return

    # Group by exercise type
    exercise_types = {}
    for record in records:
        ex_type = record.get("exercise_type", "other")
        if ex_type not in exercise_types:
            exercise_types[ex_type] = []
        exercise_types[ex_type].append(record)

    for ex_type, type_records in exercise_types.items():
        with st.expander(f"{ex_type.replace('_', ' ').title()} PRs", expanded=True):
            for record in type_records:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{record.get('exercise_name')}**")
                with col2:
                    st.write(f"{record.get('record_value')}")
                with col3:
                    achieved = record.get("achieved_at", "")
                    if achieved:
                        dt = datetime.fromisoformat(achieved.replace("Z", "+00:00"))
                        st.caption(dt.strftime("%b %d, %Y"))

    # Add PR button
    with st.expander("Add Personal Record"):
        render_add_pr_form(db)


def render_add_pr_form(db: DatabaseManager):
    """Render form to add a personal record."""
    with st.form("add_pr_form"):
        exercise_type = st.selectbox(
            "Exercise Type",
            options=["skierg", "sled_push", "sled_pull", "rowing", "wall_balls",
                     "farmers_carry", "sandbag_lunges", "burpee_broad_jump",
                     "run", "strength", "other"]
        )

        exercise_name = st.text_input("Exercise Name", placeholder="e.g., 1km Row")

        record_type = st.selectbox(
            "Record Type",
            options=["time", "weight", "reps", "distance"]
        )

        record_value = st.text_input("Record Value", placeholder="e.g., 3:45 or 100kg")

        notes = st.text_input("Notes (optional)")

        if st.form_submit_button("Save PR"):
            if exercise_name and record_value:
                db.create_personal_record(
                    exercise_type=exercise_type,
                    exercise_name=exercise_name,
                    record_type=record_type,
                    record_value=record_value,
                    notes=notes,
                )
                st.success("Personal record saved!")
                st.rerun()
            else:
                st.error("Please fill in exercise name and record value")


def render_ai_analysis(workout_results: list, db: DatabaseManager):
    """Render AI-powered analysis."""
    st.divider()
    st.subheader("AI Coach Analysis")

    with st.spinner("Analyzing your training data..."):
        try:
            # Prepare performance data
            performance_data = {
                "total_workouts": len(workout_results),
                "workout_history": [
                    {
                        "date": r.get("completed_at"),
                        "duration_mins": (r.get("total_duration_seconds") or 0) / 60,
                        "rpe": r.get("perceived_effort"),
                        "feeling": r.get("feeling"),
                    }
                    for r in workout_results[-20:]  # Last 20 workouts
                ],
                "avg_rpe": sum(r.get("perceived_effort", 0) or 0 for r in workout_results) / len(workout_results) if workout_results else 0,
                "personal_records": db.get_personal_records()[:10],
            }

            insights = get_coaching_insights(performance_data)
            st.markdown(insights)

        except Exception as e:
            st.error(f"Error getting AI analysis: {str(e)}")

    if st.button("Close Analysis"):
        st.session_state.show_ai_analysis = False
        st.rerun()
