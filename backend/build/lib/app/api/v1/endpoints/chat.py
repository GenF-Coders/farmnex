from fastapi import APIRouter
from app.core.responses import ok
router=APIRouter()
@router.get("")
async def conversations(): return ok([{ "id":"C-1001","participant":{"id":201,"name":"FreshMart Foods"},"last_message":"Can you deliver on Monday?","unread":2}])
@router.post("")
async def create_conversation(): return ok({"id":"C-1002","created":True})
@router.get("/{conversation_id}")
async def conversation(conversation_id:str): return ok({"id":conversation_id,"participant":{"id":201,"name":"FreshMart Foods"}})
@router.get("/{conversation_id}/messages")
async def messages(conversation_id:str): return ok([{ "id":"MSG-1","sender_id":201,"message":"Can you deliver on Monday?","sent_at":"2026-09-13T11:00:00Z"}])
@router.post("/{conversation_id}/messages")
async def send_message(conversation_id:str): return ok({"id":"MSG-2","conversation_id":conversation_id,"message":"Yes, delivery can be arranged."})
