import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
