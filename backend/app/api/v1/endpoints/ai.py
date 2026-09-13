from fastapi import APIRouter, UploadFile, File
from app.core.responses import ok
router=APIRouter()
@router.post("/crop-recommendation")
async def crop_recommendation(): return ok({"recommendations":[{"crop":"Tomato","score":0.91,"expected_revenue_per_acre":85000},{"crop":"Onion","score":0.86,"expected_revenue_per_acre":78000}],"reasoning":["Strong local demand","Suitable season","Expected price trend"]})
@router.get("/crop-recommendation/{recommendation_id}")
async def recommendation(recommendation_id:str): return ok({"id":recommendation_id,"status":"completed","recommendations":[{"crop":"Tomato","score":0.91}]})
@router.post("/disease-detection")
async def disease_detection(image: UploadFile | None = File(default=None)):
    return ok({"scan_id":"DS-2001","file_name":image.filename if image else None,"crop":"Tomato","disease":"Early blight","confidence":0.93,"severity":"medium","recommendations":["Remove affected leaves","Improve airflow","Consult local agricultural expert before treatment"]})
