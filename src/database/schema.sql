-- Hyrox Workout Tracker Database Schema

-- Workout Programs table (stores the parsed workout programs)
CREATE TABLE IF NOT EXISTS workout_programs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    raw_input TEXT NOT NULL,
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual workout days
CREATE TABLE IF NOT EXISTS workouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    program_id UUID REFERENCES workout_programs(id) ON DELETE CASCADE,
    day_number INTEGER NOT NULL,
    week_number INTEGER,
    scheduled_date DATE,
    title VARCHAR(255),
    workout_type VARCHAR(100), -- e.g., 'strength', 'running', 'hyrox_simulation', 'recovery'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workout exercises (individual exercises within a workout)
CREATE TABLE IF NOT EXISTS workout_exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_id UUID REFERENCES workouts(id) ON DELETE CASCADE,
    exercise_order INTEGER NOT NULL,
    exercise_name VARCHAR(255) NOT NULL,
    exercise_type VARCHAR(100), -- 'run', 'skierg', 'sled_push', 'sled_pull', 'burpee_broad_jump', 'rowing', 'farmers_carry', 'sandbag_lunges', 'wall_balls', 'strength', 'cardio'
    sets INTEGER,
    reps VARCHAR(50), -- Can be "10" or "10-12" or "AMRAP"
    weight VARCHAR(50), -- Can be "50kg" or "bodyweight" or "RPE 7"
    distance VARCHAR(50), -- For running/rowing
    duration VARCHAR(50), -- For time-based exercises
    rest_period VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workout results (tracking completed workouts)
CREATE TABLE IF NOT EXISTS workout_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_id UUID REFERENCES workouts(id) ON DELETE CASCADE,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_duration_seconds INTEGER,
    perceived_effort INTEGER CHECK (perceived_effort >= 1 AND perceived_effort <= 10), -- RPE 1-10
    heart_rate_avg INTEGER,
    heart_rate_max INTEGER,
    notes TEXT,
    feeling VARCHAR(50), -- 'great', 'good', 'okay', 'tired', 'exhausted'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Exercise results (individual exercise performance)
CREATE TABLE IF NOT EXISTS exercise_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_result_id UUID REFERENCES workout_results(id) ON DELETE CASCADE,
    workout_exercise_id UUID REFERENCES workout_exercises(id) ON DELETE CASCADE,
    sets_completed INTEGER,
    reps_completed VARCHAR(100), -- JSON array or comma-separated for multiple sets
    weight_used VARCHAR(50),
    time_seconds INTEGER,
    distance_completed VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Personal Records
CREATE TABLE IF NOT EXISTS personal_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_type VARCHAR(100) NOT NULL,
    exercise_name VARCHAR(255) NOT NULL,
    record_type VARCHAR(50) NOT NULL, -- 'weight', 'time', 'distance', 'reps'
    record_value VARCHAR(100) NOT NULL,
    achieved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    workout_result_id UUID REFERENCES workout_results(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Hyrox Race Results (for tracking actual race performance)
CREATE TABLE IF NOT EXISTS hyrox_race_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    race_date DATE NOT NULL,
    race_location VARCHAR(255),
    division VARCHAR(100), -- 'open', 'pro', 'doubles'
    total_time_seconds INTEGER NOT NULL,

    -- Individual station times (in seconds)
    run_1_time INTEGER,
    skierg_time INTEGER,
    run_2_time INTEGER,
    sled_push_time INTEGER,
    run_3_time INTEGER,
    sled_pull_time INTEGER,
    run_4_time INTEGER,
    burpee_broad_jump_time INTEGER,
    run_5_time INTEGER,
    rowing_time INTEGER,
    run_6_time INTEGER,
    farmers_carry_time INTEGER,
    run_7_time INTEGER,
    sandbag_lunges_time INTEGER,
    run_8_time INTEGER,
    wall_balls_time INTEGER,

    -- Transition times
    transitions_total_time INTEGER,

    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_workouts_program_id ON workouts(program_id);
CREATE INDEX IF NOT EXISTS idx_workouts_scheduled_date ON workouts(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_workout_exercises_workout_id ON workout_exercises(workout_id);
CREATE INDEX IF NOT EXISTS idx_workout_results_workout_id ON workout_results(workout_id);
CREATE INDEX IF NOT EXISTS idx_workout_results_completed_at ON workout_results(completed_at);
CREATE INDEX IF NOT EXISTS idx_exercise_results_workout_result_id ON exercise_results(workout_result_id);
CREATE INDEX IF NOT EXISTS idx_personal_records_exercise_type ON personal_records(exercise_type);

-- Enable Row Level Security (optional, for multi-user support)
-- ALTER TABLE workout_programs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE workouts ENABLE ROW LEVEL SECURITY;
-- etc.
