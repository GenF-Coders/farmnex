# 🌾 FarmNex

### AI-Powered Direct Agricultural Marketplace & Supply Chain Platform

> Built for Smart India Hackathon 2026  
> Problem Statement ID: 26033  
> Theme: Agriculture, FoodTech & Rural Development

---

## 🚜 About FarmNex

FarmNex is an AI-powered agricultural marketplace designed to connect
farmers and Farmer Producer Organisations (FPOs) directly with bulk
buyers and customers.

The platform aims to reduce unnecessary intermediaries in the
agricultural value chain while improving price discovery, reducing
post-harvest losses, creating value from agricultural waste, and
optimizing logistics.

FarmNex brings the complete process together in one platform:

**Price Discovery → Buyer Matching → Pre-Bidding → Crop Rescue →
Waste-to-Wealth → AI Forecasting → Route Optimization → Delivery**

---

## 🎯 Problem

Traditional agricultural supply chains can involve multiple
intermediaries between farmers and consumers.

A typical chain may involve:

Farmer → Local Agent → Wholesaler → Retailer → Consumer

Each additional layer can increase the gap between the price received
by the farmer and the price paid by the consumer.

FarmNex addresses this challenge by enabling more direct and transparent
connections between farmers, FPOs, buyers and customers.

---

## 💡 Our Solution

FarmNex provides a unified digital platform where farmers can:

- List and manage their crops
- Connect directly with buyers
- Receive bids before harvest
- Find suitable buyers based on price and demand
- Rescue crops that are close to spoilage
- Sell agricultural waste for productive use
- Get AI-powered price and demand forecasts
- Receive crop planning recommendations
- Optimize delivery routes
- Aggregate produce through FPOs

---

# 🚀 Core Features

## 1. 🔨 Pre-Bidding

Farmers can list crops before harvest with expected quantity,
harvest date and expected price.

Verified buyers can place competitive bids.

The farmer can compare bids and select the most suitable offer.

---

## 2. 🤝 Direct Farmer-to-Buyer Marketplace

Farmers and FPOs can directly connect with:

- Bulk buyers
- Businesses
- Retailers
- Customers

The platform provides transparent crop information and buyer
discovery.

---

## 3. 🚨 Crop Rescue

Crops that are approaching spoilage can be marked as rescue
opportunities.

FarmNex helps identify potential buyers who may be able to purchase
the produce quickly.

This aims to reduce avoidable post-harvest losses.

---

## 4. ♻️ Waste to Wealth

Agricultural waste can become an additional source of income.

FarmNex enables farmers to list suitable agricultural waste for
potential applications such as:

- Compost
- Cattle feed
- Biogas
- Other agricultural/industrial uses

---

## 5. 🤖 AI Forecaster

FarmNex uses AI/ML capabilities to provide agricultural decision
support.

### Price Prediction

Estimate future crop prices using relevant historical and market
information.

### Demand Forecasting

Estimate where and when demand for a crop may increase.

### Crop Planning

Recommend potentially suitable crops based on demand and relevant
agricultural factors.

### Price Recommendation

Provide an AI-assisted reference price to support better price
discovery.

### Crop Disease Prediction

Planned AI capability for identifying potential crop diseases from
crop images and providing appropriate next-step guidance.

---

## 6. 🎯 Smart Buyer Matching

FarmNex can rank potential buyers using factors such as:

- Offered price
- Demand
- Required quantity
- Location
- Delivery requirements
- Buyer history

---

## 7. 🚚 Route Optimization

FarmNex can optimize transportation by considering nearby farms,
buyers and delivery requirements.

The objective is to reduce:

- Transportation cost
- Travel time
- Empty vehicle capacity
- Unnecessary routes

---

## 8. 👨‍🌾 FPO Aggregation

Small farms can be aggregated through FPOs into larger lots.

This can help farmers meet bulk-buyer quantity requirements and
increase collective bargaining power.

---

# 👥 User Roles

## Farmer

- Register and manage profile
- Add crops
- List fresh produce
- Participate in pre-bidding
- Accept buyer bids
- Use AI forecasting
- List agricultural waste
- Request crop rescue
- Track transactions and deliveries

## FPO

- Manage multiple farmers
- Aggregate crops
- Create bulk lots
- Coordinate sales
- Connect with bulk buyers

## Buyer

- Browse available crops
- Search by crop, quantity and location
- Place bids
- Purchase directly from farmers/FPOs
- Manage orders
- Track deliveries

## Customer

- Discover available produce
- Purchase eligible crops
- View seller and product information
- Track orders

---

# 🧠 AI & Data Intelligence

FarmNex is designed around multiple agricultural intelligence
capabilities:

| AI Capability | Purpose |
|---|---|
| Price Prediction | Estimate future crop prices |
| Demand Forecasting | Predict upcoming crop demand |
| Price Recommendation | Support farmer price discovery |
| Crop Planning | Suggest potentially profitable crops |
| Crop Disease Detection | Identify possible crop diseases |
| Buyer Matching | Rank suitable buyers |
| Route Optimization | Reduce logistics cost and time |

---

# 🏗️ Technology Stack

### Frontend

- Flutter
- Dart

### Backend

- Python
- FastAPI
- REST APIs

### AI / Machine Learning

- Python
- Machine Learning models
- Data processing and forecasting

### Database

- MySQL

### Maps & Logistics

- Google Maps API
- OR-Tools

### Cloud & Services

- FastAPI Cloud
- Firebase / AWS where required

---

# 🏛️ System Architecture

```text
                    ┌───────────────────┐
                    │   Flutter App     │
                    │ Farmer / Buyer /  │
                    │ Customer / FPO    │
                    └─────────┬─────────┘
                              │
                              │ REST API
                              ▼
                    ┌───────────────────┐
                    │      FastAPI      │
                    │    Backend API    │
                    └─────────┬─────────┘
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
        ┌──────────┐   ┌──────────────┐  ┌──────────────┐
        │  MySQL   │   │   AI / ML    │  │ External APIs│
        │ Database │   │   Services   │  │ Maps/Weather │
        └──────────┘   └──────────────┘  └──────────────┘


backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── core/                                      # Global infrastructure
│   │   ├── __init__.py
│   │   ├── config.py                              # Environment/settings
│   │   ├── database.py                            # DB engine/session
│   │   ├── security.py                            # JWT/password hashing
│   │   ├── logging.py                             # Logging configuration
│   │   ├── exceptions.py                          # Global exceptions
│   │   ├── middleware.py                          # CORS/request middleware
│   │   └── constants.py                           # Global constants/enums
│   │
│   ├── api/                                       # HTTP/API layer
│   │   ├── __init__.py
│   │   ├── deps.py                                # Common dependencies
│   │   │
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py                          # Registers all v1 endpoints
│   │   │   │
│   │   │   └── endpoints/                         # HTTP endpoint definitions
│   │   │       ├── __init__.py
│   │   │       ├── health.py
│   │   │       ├── auth.py
│   │   │       ├── users.py
│   │   │       ├── farmers.py
│   │   │       ├── buyers.py
│   │   │       ├── fpos.py
│   │   │       ├── verification.py
│   │   │       ├── locations.py
│   │   │       ├── farms.py
│   │   │       ├── crop_types.py
│   │   │       ├── crops.py
│   │   │       ├── crop_images.py
│   │   │       ├── inventory.py
│   │   │       ├── marketplace.py
│   │   │       ├── bids.py
│   │   │       ├── rescue.py
│   │   │       ├── waste.py
│   │   │       ├── orders.py
│   │   │       ├── payments.py
│   │   │       ├── deliveries.py
│   │   │       ├── routes.py
│   │   │       ├── forecasting.py
│   │   │       ├── prices.py
│   │   │       ├── ai.py
│   │   │       ├── matching.py
│   │   │       ├── notifications.py
│   │   │       ├── favorites.py
│   │   │       ├── reviews.py
│   │   │       ├── chat.py
│   │   │       ├── dashboards.py
│   │   │       ├── uploads.py
│   │   │       ├── market_data.py
│   │   │       ├── weather.py
│   │   │       ├── soil.py
│   │   │       ├── search.py
│   │   │       ├── recommendations.py
│   │   │       ├── analytics.py
│   │   │       ├── admin.py
│   │   │       └── webhooks.py
│   │   │
│   │   └── v2/                                   # Only for future breaking changes
│   │       ├── __init__.py
│   │       └── router.py
│   │
│   ├── modules/                                  # Business/domain layer
│   │   │
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   ├── exceptions.py
│   │   │   └── constants.py
│   │   │
│   │   ├── users/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── farmers/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   │
│   │   ├── buyers/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   │
│   │   ├── fpos/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   │
│   │   ├── crops/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── inventory/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   │
│   │   ├── bidding/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── rescue/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   │
│   │   ├── waste/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   │
│   │   ├── marketplace/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   │
│   │   ├── orders/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── payments/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── deliveries/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   │
│   │   ├── forecasting/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   │
│   │   ├── matching/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   │
│   │   ├── notifications/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   │
│   │   ├── reviews/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   │
│   │   ├── chat/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   └── service.py
│   │   │
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── disease.py
│   │   │   ├── demand.py
│   │   │   ├── price.py
│   │   │   └── crop_planning.py
│   │   │
│   │   ├── analytics/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   └── service.py
│   │   │
│   │   └── verification/
│   │       ├── __init__.py
│   │       ├── models.py
│   │       ├── schemas.py
│   │       ├── repository.py
│   │       └── service.py
│   │
│   ├── integrations/                              # External services
│   │   ├── __init__.py
│   │   ├── redis.py
│   │   ├── storage.py                             # S3/object storage
│   │   ├── email.py
│   │   ├── sms.py
│   │   ├── payment_gateway.py
│   │   ├── maps.py                                # Google Maps/etc.
│   │   ├── weather.py
│   │   ├── market_data.py
│   │   └── push_notifications.py
│   │
│   ├── workers/                                   # Background jobs
│   │   ├── __init__.py
│   │   ├── celery.py
│   │   └── tasks/
│   │       ├── __init__.py
│   │       ├── emails.py
│   │       ├── notifications.py
│   │       ├── market_sync.py
│   │       ├── weather_sync.py
│   │       ├── forecasts.py
│   │       └── cleanup.py
│   │
│   └── utils/                                     # Generic helpers
│       ├── __init__.py
│       ├── pagination.py
│       ├── datetime.py
│       ├── validators.py
│       ├── response.py
│       └── enums.py
│
├── models/                                        # Optional central model exports
│   └── __init__.py
│
├── schemas/                                       # Optional shared schemas
│   └── __init__.py
│
├── repositories/                                  # Optional shared repositories
│   └── __init__.py
│
├── db/
│   ├── __init__.py
│   └── seed/
│       └── README.md
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   │
│   ├── unit/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── farmers/
│   │   ├── buyers/
│   │   ├── crops/
│   │   ├── bidding/
│   │   ├── orders/
│   │   ├── payments/
│   │   ├── forecasting/
│   │   └── matching/
│   │
│   ├── integration/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   └── v2/
│   │   └── database/
│   │
│   └── e2e/
│
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 001_create_users.py
│       ├── 002_create_farms.py
│       ├── 003_create_crops.py
│       ├── 004_create_bids.py
│       ├── 005_create_orders.py
│       └── ...
│
├── scripts/
│   ├── seed.py
│   ├── create_admin.py
│   ├── migrate.py
│   └── cleanup.py
│
├── deployment/
│   ├── docker/
│   │   └── Dockerfile
│   ├── nginx/
│   │   └── nginx.conf
│   └── k8s/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── ingress.yaml
│
├── .github/
│   └── workflows/
│       ├── tests.yml
│       ├── lint.yml
│       └── deploy.yml
│
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── API_NOTES.md
├── README.md
└── Makefile