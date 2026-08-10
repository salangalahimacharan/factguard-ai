import os
import sys

# Add backend directory to Python sys.path so app imports resolve cleanly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
