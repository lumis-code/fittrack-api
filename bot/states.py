from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    waiting_for_contact = State()


class WorkoutStates(StatesGroup):
    choosing_type = State()
    gym_exercise_name = State()
    gym_muscle_group = State()
    gym_sets = State()
    gym_reps = State()
    gym_weight = State()
    run_distance = State()
    run_duration_time = State()
    run_elevation = State()
    swim_distance = State()
    swim_pool_length = State()
    swim_strokes = State()
    swim_heart_rate = State()
    common_duration = State()
    common_notes = State()
