from fastapi import FastAPI

app = FastAPI(title="T-Level AWS Academy API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
