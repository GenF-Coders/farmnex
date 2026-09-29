from fastapi import APIRouter
from app.api.v2.endpoints import crop_type_controller, farm_crop_controller, farm_crop_activity_controller, crop_batch_controller, product_listing_controller, product_image_controller, buyer_demand_request_controller, bid_event_controller, bid_controller, order_controller, order_item_controller, payment_controller, delivery_controller, delivery_tracking_event_controller, delivery_proof_controller, waste_record_controller, waste_utilization_listing_controller, ai_prediction_controller, ai_recommendation_controller, notification_controller, review_controller, order_dispute_controller, audit_log_controller

router = APIRouter()

modules = [
    crop_type_controller,
    farm_crop_controller,
    farm_crop_activity_controller,
    crop_batch_controller,
    product_listing_controller,
    product_image_controller,
    buyer_demand_request_controller,
    bid_event_controller,
    bid_controller,
    order_controller,
    order_item_controller,
    payment_controller,
    delivery_controller,
    delivery_tracking_event_controller,
    delivery_proof_controller,
    waste_record_controller,
    waste_utilization_listing_controller,
    ai_prediction_controller,
    ai_recommendation_controller,
    notification_controller,
    review_controller,
    order_dispute_controller,
    audit_log_controller
]

for module in modules:
    router.include_router(module.router)
