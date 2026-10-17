from fastapi import FastAPI

app = FastAPI(
    title="Forensic Investigation System",
    description="AI-Powered Crime Investigation & Forensic Evidence Management System",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Forensic Investigation System API is running"
    }