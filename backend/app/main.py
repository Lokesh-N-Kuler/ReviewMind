import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import auth, projects, reviews, memory, github, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("reviewmind")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing ReviewMind database schemas...")
    try:
        init_db()
        logger.info("Database schemas initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database schemas: {e}")
    yield
    logger.info("ReviewMind backend shutting down.")

app = FastAPI(
    title="ReviewMind API",
    description="AI-Powered Code Review Agent with Persistent Memory using Hindsight",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS configuration
origins = [
    settings.FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(reviews.router)
app.include_router(memory.router)
app.include_router(github.router)

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_url": "/api/health",
        "description": "AI-Powered Code Review Agent with Persistent Memory using Hindsight and Groq."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
