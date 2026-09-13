from fastapi import APIRouter, UploadFile, File
from app.core.responses import ok
router=APIRouter()
@router.post("")
async def upload(file: UploadFile = File(...)):
    return ok({"file_id":"FILE-1001","file_name":file.filename,"content_type":file.content_type,"url":"https://cdn.example.com/farmnex/FILE-1001"},"File uploaded")
@router.get("/{file_id}")
async def get_file(file_id:str): return ok({"file_id":file_id,"url":f"https://cdn.example.com/farmnex/{file_id}"})
@router.delete("/{file_id}")
async def delete_file(file_id:str): return ok({"file_id":file_id,"deleted":True})
