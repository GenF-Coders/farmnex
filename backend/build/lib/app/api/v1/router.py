from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, farmers, buyers, fpos, locations, farms, verification, crops, inventory, marketplace, bids, rescue, waste, orders, payments, deliveries, routes, forecasting, prices, ai, matching, notifications, favorites, reviews, chat, dashboard, admin, uploads, external_data, search, analytics, webhooks

router = APIRouter()

modules = [
    (auth, "/auth", "Authentication"), (users, "/users", "Users"),
    (farmers, "/farmers", "Farmers"), (buyers, "/buyers", "Buyers"),
    (fpos, "/fpos", "FPOs"), (locations, "/locations", "Locations"),
    (farms, "/farms", "Farms"), (verification, "/verification", "Verification"),
    (crops, "/crops", "Crops"), (inventory, "/inventory", "Inventory"),
    (marketplace, "/marketplace", "Marketplace"), (bids, "/bids", "Bids"),
    (rescue, "/rescue", "Crop Rescue"), (waste, "/waste", "Waste to Wealth"),
    (orders, "/orders", "Orders"), (payments, "/payments", "Payments"),
    (deliveries, "/deliveries", "Deliveries"), (routes, "/routes", "Route Planning"),
    (forecasting, "/forecast", "Forecasting"), (prices, "/prices", "Price Discovery"),
    (ai, "/ai", "AI Services"), (matching, "/matching", "Buyer Matching"),
    (notifications, "/notifications", "Notifications"), (favorites, "/favorites", "Favorites"),
    (reviews, "/reviews", "Reviews"), (chat, "/conversations", "Chat"),
    (dashboard, "/dashboard", "Dashboards"), (admin, "/admin", "Administration"),
    (uploads, "/uploads", "Uploads"), (external_data, "/external-data", "External Data"),
    (search, "/search", "Search & Recommendations"), (analytics, "/analytics", "Analytics"),
    (webhooks, "/webhooks", "Webhooks"),
]

for module, prefix, tag in modules:
    router.include_router(module.router, prefix=prefix, tags=[tag])
