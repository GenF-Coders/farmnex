from fastapi import APIRouter

from app.api.v2.endpoints import (
    auth_controller,
    role_controller,
    user_controller,
    storage_controller,
    address_controller,
    farm_controller,
    otp_controller,

    # AI
    ai_prediction_controller,
    ai_recommendation_controller,

    # Audit
    audit_log_controller,

    # Marketplace / Trading
    bid_controller,
    bid_event_controller,
    buyer_demand_request_controller,

    # Crops
    crop_batch_controller,
    crop_type_controller,
    farm_crop_controller,
    farm_crop_activity_controller,

    # Orders / Deliveries
    order_controller,
    order_item_controller,
    order_dispute_controller,
    delivery_controller,
    delivery_proof_controller,
    delivery_tracking_event_controller,

    # Payments
    payment_controller,

    # Products
    product_listing_controller,
    product_image_controller,
    listing_media_controller,

    # Notifications / Reviews
    notification_controller,
    review_controller,

    # Waste Management
    waste_record_controller,
    waste_utilization_listing_controller,
    
    home_controller,
    me_controller
)


router = APIRouter()


# Unmounted modules (F1 fast path, approved in docs/STATUS.md 2026-09-29): their routes had no
# ownership checks, and no screen or demo step uses them. Code and tables stay. Re-mount one only
# together with its F1 ownership fix.
modules = [
    
    # Authentication and users
    auth_controller,
    #role_controller,
    user_controller,
    storage_controller,
    address_controller,
    farm_controller,
    #otp_controller,
    
    
    #Home
    home_controller,
    me_controller,
    
    
    # Crops
    crop_type_controller,
    farm_crop_controller,
    crop_batch_controller,
    #farm_crop_activity_controller,  # unmounted (F1 fast path)
    
    
    # Products
    product_listing_controller,
    product_image_controller,
    listing_media_controller,
    
    
    # Waste Management
    waste_record_controller,
    waste_utilization_listing_controller,
    
    
    # Notifications / Reviews
    notification_controller,
    #review_controller,  # unmounted (F1 fast path)
    
    
     # Marketplace / Trading
    bid_controller,
    bid_event_controller,
    buyer_demand_request_controller,
    
     
    # Orders / Deliveries
    order_controller,
    order_item_controller,
    #order_dispute_controller,  # unmounted (F1 fast path)
    #delivery_controller,  # unmounted (F1 fast path)
    #delivery_proof_controller,  # unmounted (F1 fast path)
    #delivery_tracking_event_controller,  # unmounted (F1 fast path)


    # Payments
    payment_controller,

    
    # AI
    #ai_prediction_controller,  # unmounted (F1 fast path)
    #ai_recommendation_controller,  # unmounted (F1 fast path)

    # Audit
    #audit_log_controller,  # unmounted (F1 fast path)
]


for module in modules:
    router.include_router(module.router)