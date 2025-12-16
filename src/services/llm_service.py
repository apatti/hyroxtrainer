import os
import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")


def get_llm_client():
    """Get the appropriate LLM client based on configuration."""
    if LLM_PROVIDER == "openai":
        from openai import OpenAI
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    elif LLM_PROVIDER == "anthropic":
        import anthropic
        return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    else:
        # Gemini (default)
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        return genai


def call_llm(system_prompt: str, user_prompt: str, json_response: bool = False) -> str:
    """Call the LLM with the given prompts."""
    client = get_llm_client()

    if LLM_PROVIDER == "openai":
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"} if json_response else None,
            temperature=0.3,
        )
        return response.choices[0].message.content
    elif LLM_PROVIDER == "anthropic":
        full_prompt = user_prompt
        if json_response:
            full_prompt += "\n\nRespond with valid JSON only, no other text."

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            system=system_prompt,
            messages=[{"role": "user", "content": full_prompt}],
        )
        return response.content[0].text
    else:
        # Gemini
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        if json_response:
            full_prompt += "\n\nRespond with valid JSON only, no other text."

        model = client.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 8000,
            }
        )
        response = model.generate_content(full_prompt)
        return response.text


WORKOUT_PARSER_SYSTEM_PROMPT = """You are an expert fitness coach specializing in Hyrox training.
Your task is to parse workout program descriptions into structured JSON format.

Hyrox is a fitness race combining running with functional workout stations:
- 8 x 1km runs
- SkiErg (1000m)
- Sled Push (50m)
- Sled Pull (50m)
- Burpee Broad Jumps (80m)
- Rowing (1000m)
- Farmers Carry (200m)
- Sandbag Lunges (100m)
- Wall Balls (100 reps for men, 75 for women)

When parsing workouts, identify:
1. Individual training days/sessions
2. Exercise names and types
3. Sets, reps, weight, distance, duration
4. Rest periods
5. Any special notes or instructions

Exercise types should be categorized as:
- run, skierg, sled_push, sled_pull, burpee_broad_jump, rowing, farmers_carry, sandbag_lunges, wall_balls (Hyrox specific)
- strength, cardio, mobility, recovery (general categories)

Always output valid JSON matching the requested schema."""


def parse_workout_program(raw_text: str, program_name: str, start_date: Optional[str] = None) -> dict:
    """Parse raw workout text into structured format using LLM."""

    user_prompt = f"""Parse the following workout program into structured JSON format.

Program Name: {program_name}
Start Date: {start_date or "Not specified - use day numbers only"}

Workout Text:
{raw_text}

Return a JSON object with this structure:
{{
    "program": {{
        "name": "{program_name}",
        "description": "Brief description of the program",
        "total_weeks": number or null,
        "total_days": number
    }},
    "workouts": [
        {{
            "day_number": 1,
            "week_number": 1 or null,
            "scheduled_date": "YYYY-MM-DD" or null,
            "title": "Workout title",
            "workout_type": "strength|running|hyrox_simulation|recovery|mixed",
            "description": "Brief description of this workout",
            "exercises": [
                {{
                    "exercise_order": 1,
                    "exercise_name": "Exercise name",
                    "exercise_type": "run|skierg|sled_push|etc",
                    "sets": number or null,
                    "reps": "10" or "10-12" or "AMRAP" or null,
                    "weight": "50kg" or "bodyweight" or null,
                    "distance": "1km" or null,
                    "duration": "30 seconds" or null,
                    "rest_period": "60 seconds" or null,
                    "notes": "Any special instructions" or null
                }}
            ]
        }}
    ]
}}

If a start_date is provided, calculate scheduled_date for each workout day.
Be thorough and capture all exercises mentioned."""

    response = call_llm(WORKOUT_PARSER_SYSTEM_PROMPT, user_prompt, json_response=True)

    # Clean up response if needed
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]

    return json.loads(response)


COACHING_SYSTEM_PROMPT = """You are an expert Hyrox coach providing personalized training guidance.
Your role is to analyze workout performance data and provide actionable insights.

Consider:
1. Progress trends over time
2. Weaknesses in specific Hyrox stations
3. Recovery and training balance
4. Race preparation strategies
5. Technique improvements

Be encouraging but honest. Provide specific, actionable recommendations.
Keep responses concise and focused on the most important insights."""


def get_coaching_insights(performance_data: dict, question: Optional[str] = None) -> str:
    """Get coaching insights based on performance data."""

    user_prompt = f"""Analyze this Hyrox training performance data and provide coaching insights:

Performance Data:
{json.dumps(performance_data, indent=2)}

{"User Question: " + question if question else "Provide a general analysis with key insights and recommendations."}

Focus on:
1. Overall progress assessment
2. Strongest and weakest areas
3. Top 3 specific recommendations for improvement
4. Any concerns or areas needing attention

Keep response under 500 words and format with clear sections."""

    return call_llm(COACHING_SYSTEM_PROMPT, user_prompt)


def get_workout_guidance(workout: dict, past_performance: Optional[dict] = None) -> str:
    """Get guidance for a specific workout based on past performance."""

    user_prompt = f"""Provide guidance for today's workout:

Workout Details:
{json.dumps(workout, indent=2)}

{"Past Performance for Similar Exercises:" + json.dumps(past_performance, indent=2) if past_performance else "No past performance data available."}

Provide:
1. Brief warmup recommendations
2. Pacing strategy for this workout
3. Key technique focus points
4. Target metrics based on past performance (if available)
5. Post-workout recovery tips

Keep response concise and actionable."""

    return call_llm(COACHING_SYSTEM_PROMPT, user_prompt)


def analyze_race_performance(race_result: dict, training_history: Optional[dict] = None) -> str:
    """Analyze a Hyrox race result and provide insights."""

    user_prompt = f"""Analyze this Hyrox race performance:

Race Result:
{json.dumps(race_result, indent=2)}

{"Recent Training History:" + json.dumps(training_history, indent=2) if training_history else ""}

Provide:
1. Overall race analysis
2. Station-by-station breakdown (identify fastest/slowest)
3. Transition time analysis
4. Comparison to typical Hyrox benchmarks
5. Specific training focus areas for next race
6. Predicted improvement areas with targeted training

Format clearly with sections."""

    return call_llm(COACHING_SYSTEM_PROMPT, user_prompt)
