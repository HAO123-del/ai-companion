"""
AI Companion Backend - FastAPI Application
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system env vars

from database import engine, Base
from routers import companions, messages, memories, reminders, books, diary, games, voice, call, music

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Companion API",
    description="Backend API for AI Companion application",
    version="1.0.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(companions.router, prefix="/api/companions", tags=["Companions"])
app.include_router(messages.router, prefix="/api/messages", tags=["Messages"])
app.include_router(memories.router, prefix="/api/memories", tags=["Memories"])
app.include_router(reminders.router, prefix="/api/reminders", tags=["Reminders"])
app.include_router(books.router, prefix="/api/books", tags=["Books"])
app.include_router(diary.router, prefix="/api/diary", tags=["Diary"])
app.include_router(games.router, prefix="/api/games", tags=["Games"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])
app.include_router(call.router, prefix="/api/call", tags=["Call"])
app.include_router(music.router, prefix="/api/music", tags=["Music"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "AI Companion API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}


@app.get("/api/health")
async def api_health_check():
    """API Health check endpoint for Render"""
    return {"status": "healthy", "service": "ai-companion-api"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
