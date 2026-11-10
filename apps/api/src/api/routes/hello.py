from fastapi import APIRouter

router = APIRouter()

@router.get("/v1/hello")
def hello():
    return {"message": "Hello World", "service": "TrendyReports API"}
