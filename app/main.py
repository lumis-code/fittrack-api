from fastapi import FastAPI

from app.routers.analytics import router as analytics_router
from app.routers.users import router as users_router
from app.routers.workouts import router as workouts_router

app = FastAPI(title="FitTrack API")
app.include_router(users_router)
app.include_router(analytics_router)
app.include_router(workouts_router)
