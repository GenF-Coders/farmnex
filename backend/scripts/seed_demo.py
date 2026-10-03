"""Make the demo data through FarmNex's public API (S34).

What it builds (docs/integration/route-optimizer.md -> "Demo seed"):
  driver vehicle near Pune -> two farmers each with a farm + Tomato listing -> the buyer's drop address
  -> one checkout with both farmers' listings -> Pay (demo) -> each farmer confirms their order
  -> the manager books transport -> pending loads, ready for the driver to plan a pooled trip.
Also, so those screens are not empty: two open pre-bids per farmer (the buyer bids on each) and three
Crop Rescue lots per farmer (one Tomato lot close to spoiling).

It only calls /api/v2 endpoints, with login tokens read from environment variables. It never touches
the database, never prints a token and never writes one to a file. Running it twice does not make
duplicates (listings, farms, vehicle, address are looked up first; a checkout is only made if the
listings still have the stock for it).

Tokens (log each demo account in yourself, then paste into YOUR OWN terminal):
  FARMNEX_TOKEN_FARMER_1  FARMNEX_TOKEN_FARMER_2  FARMNEX_TOKEN_BUYER  FARMNEX_TOKEN_DRIVER
  FARMNEX_TOKEN_MANAGER (optional: without it the farmers book their own transport)
  FARMNEX_API_URL (optional, default https://farmnex-a.fastapicloud.dev)

Run from backend/:  python scripts/seed_demo.py [--round 2] [--checkouts 1] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone

DEFAULT_URL = "https://farmnex-a.fastapicloud.dev"
PREFIX = "/api/v2"

# Everything near Pune: the trip planner only pools loads within 30 km of the truck's base.
VEHICLE = {
    "vehicle_number": "MH12DM2026",
    "vehicle_type": "mini_truck",
    "capacity_kg": 1500,
    "refrigerated": False,
    "rate_per_ton_km": 12,
    "base_lat": 18.5204,
    "base_lng": 73.8567,
    "base_label": "Pune - demo truck base",
}
FARMS = {
    "FARMER_1": dict(
        farm_name="Demo Farm Hadapsar", address_line_1="Survey 12, Hadapsar", village="Hadapsar",
        city="Pune", district="Pune", state="Maharashtra", postal_code="411028",
        latitude=18.5018, longitude=73.9423,
    ),
    "FARMER_2": dict(
        farm_name="Demo Farm Khadakwasla", address_line_1="Survey 7, Khadakwasla", village="Khadakwasla",
        city="Pune", district="Pune", state="Maharashtra", postal_code="411024",
        latitude=18.4420, longitude=73.7640,
    ),
}
DROP_ADDRESS = dict(
    address_line_1="FarmNex Demo Drop, Shivajinagar", city="Pune", district="Pune", state="Maharashtra",
    postal_code="411005", latitude=18.5308, longitude=73.8475, is_default=True,
)
CROP = "Tomato"
LISTING_KG = 500
LINE_KG = 100
PRICE_PER_KG = 24
PREBID_KG = 200
# (crop code, kg, hours since harvest), stored at 25 C. Tomato then keeps about 96 h, and a lot is
# "at risk" once 60 h or less are left, so the 44-50 h old Tomato lots are at risk and the others
# fresh (run the seed on the demo morning: the lots keep ageing). Each farmer sees only their own lots.
RESCUE_TEMP_C = 25
RESCUE_LOTS = {
    "FARMER_1": [("tomato", 480, 50), ("capsicum", 180, 10), ("cucumber", 260, 6)],
    "FARMER_2": [("tomato", 320, 44), ("cauliflower", 300, 8), ("capsicum", 150, 20)],
}


class ApiError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(f"{status}: {detail}")
        self.status = status


class Api:
    """A tiny client for one account. The token lives only in memory."""

    def __init__(self, base_url: str, token: str, label: str):
        self.base = base_url.rstrip("/") + PREFIX
        self._token = token
        self.label = label

    def call(self, method: str, path: str, body: dict | None = None, query: str = ""):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"{self.base}{path}{query}", data=data, method=method,
            headers={"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                detail = json.loads(raw).get("detail", raw.decode(errors="replace"))
            except ValueError:
                detail = raw.decode(errors="replace")
            raise ApiError(exc.code, str(detail)[:300]) from None
        except urllib.error.URLError as exc:
            raise ApiError(0, f"cannot reach the server ({exc.reason})") from None
        return json.loads(raw) if raw else None

    def get(self, path: str, query: str = ""):
        return self.call("GET", path, query=query)

    def post(self, path: str, body: dict | None = None):
        return self.call("POST", path, body if body is not None else {})


def load_apis(names: list[str], optional: tuple[str, ...] = ()) -> dict[str, Api]:
    base = os.environ.get("FARMNEX_API_URL", DEFAULT_URL)
    apis, missing = {}, []
    for name in (*names, *optional):
        token = os.environ.get(f"FARMNEX_TOKEN_{name}", "").strip()
        if token:
            apis[name] = Api(base, token, name)
        elif name not in optional:
            missing.append(f"FARMNEX_TOKEN_{name}")
    if missing:
        sys.exit("Missing environment variable(s): " + ", ".join(missing) + "\nSee docs/DEMO.md, 'Tokens'.")
    return apis


def step(msg: str) -> None:
    print(f"- {msg}")


def check_login(api: Api) -> None:
    try:
        api.get("/addresses", "?limit=1")
    except ApiError as exc:
        if exc.status in (401, 403):
            sys.exit(f"The {api.label} token was refused ({exc.status}). It may have expired (24 h): log in again.")
        raise


# ----------------------------------------------------------------------------------- the steps
def ensure_vehicle(driver: Api, dry: bool) -> dict | None:
    vehicles = driver.get("/logistics/my-vehicles")
    for v in vehicles:
        if v["vehicle_number"] == VEHICLE["vehicle_number"]:
            step(f"driver: truck {v['vehicle_number']} already registered")
            vehicle = v
            break
    else:
        if dry:
            step("driver: would register the demo truck")
            return None
        vehicle = driver.post("/logistics/vehicles", VEHICLE)
        step(f"driver: registered truck {vehicle['vehicle_number']}")
    if vehicle["status"] == "offline" and not dry:
        vehicle = driver.call("PATCH", f"/routes/vehicles/{vehicle['id']}/status", {"status": "available"})
        step("driver: truck is online")
    return vehicle


def ensure_farm(api: Api, who: str) -> dict:
    spec = FARMS[who]
    for farm in api.get("/farms", "?limit=100")["items"]:
        if farm["farm_name"] == spec["farm_name"]:
            step(f"{who}: farm '{spec['farm_name']}' exists")
            if farm.get("latitude") is None or farm.get("longitude") is None:
                print(f"  ! this farm has no map location: transport can't be booked for it")
            return farm
    farm = api.post("/farms", spec)
    step(f"{who}: created farm '{spec['farm_name']}'")
    return farm


def tomato_type(api: Api) -> str:
    for ct in api.get("/crop-types", "?limit=100"):
        if ct["name"].strip().lower() == CROP.lower() and ct["is_active"]:
            return ct["public_id"]
    sys.exit(f"Crop type '{CROP}' not found. Ask Atharv: it is the demo crop (FIX_PLAN F18).")


def ensure_batch(api: Api, who: str, farm: dict, crop_type_id: str, rnd: int) -> dict:
    variety = f"Demo Tomato R{rnd}"
    code = f"DEMO-{who.replace('_', '')}-R{rnd}"

    crops = [c for c in api.get("/farm-crops", "?limit=100") if c.get("variety") == variety]
    if crops:
        farm_crop = crops[0]
    else:
        farm_crop = api.post("/farm-crops", {
            "farm_id": farm["public_id"], "crop_type_id": crop_type_id, "variety": variety,
            "area_value": 1, "area_unit": "acre", "status": "ACTIVE",
        })
        step(f"{who}: added the crop to the farm")

    batches = [b for b in api.get("/crop-batches", "?limit=100") if b["batch_code"] == code]
    if batches:
        return batches[0]
    batch = api.post("/crop-batches", {
        "farm_crop_id": farm_crop["public_id"], "batch_code": code,
        "harvest_date": date.today().isoformat(), "quantity": LISTING_KG * 2, "unit": "kg",
        "quality_grade": "A",
    })
    step(f"{who}: made batch {code}")
    return batch


def ensure_listing(api: Api, who: str, farm: dict, batch: dict, title: str, *,
                   listing_type: str = "FIXED_PRICE", quantity: float = LISTING_KG) -> dict:
    for listing in api.get("/product-listings", "?mine=true&limit=100"):
        if listing["title"] == title:
            step(f"{who}: listing '{title}' exists ({listing['available_quantity']} kg left, {listing['status']})")
            return listing
    listing = api.post("/product-listings", {
        "farm_id": farm["public_id"], "crop_batch_id": batch["public_id"], "title": title,
        "description": "Demo data for the FarmNex finale", "listing_type": listing_type,
        "price": PRICE_PER_KG, "quantity": quantity, "unit": "kg", "minimum_order_quantity": 10,
    })
    step(f"{who}: listed '{title}' at Rs {PRICE_PER_KG}/kg")
    return listing


def ensure_bid_event(api: Api, who: str, listing: dict) -> dict:
    """An open pre-bid on the listing, for the next 5 days."""
    for event in api.get("/bid-events", "?mine=true&limit=100"):
        if event["listing_id"] == listing["public_id"] and event["status"] == "ACTIVE":
            return event
    now = datetime.now(timezone.utc)
    event = api.post("/bid-events", {
        "listing_id": listing["public_id"],
        "starts_at": (now - timedelta(minutes=1)).isoformat(),
        "ends_at": (now + timedelta(days=5)).isoformat(),
        "starting_price": PRICE_PER_KG - 4, "minimum_increment": 1,
    })
    step(f"{who}: opened pre-bidding on '{listing['title']}'")
    return event


def ensure_bid(buyer: Api, event: dict, amount: float) -> None:
    if any(b["bid_event_id"] == event["public_id"] for b in buyer.get("/bids", "?limit=100")):
        return
    try:
        buyer.post("/bids", {"bid_event_id": event["public_id"], "amount": amount, "quantity": 50})
        step(f"buyer: bid Rs {amount}/kg on a pre-bid")
    except ApiError as exc:
        print(f"  ! bid not placed: {exc}")


def ensure_rescue_lots(api: Api, who: str, farm: dict) -> None:
    """A few Crop Rescue lots per farmer: one Tomato close to spoiling, the others still fresh."""
    lots = api.get("/rescue/lots")
    have = {(l["crop_code"], round(float(l["quantity_kg"]))) for l in lots}
    now = datetime.now(timezone.utc)
    for crop, kg, hours_ago in RESCUE_LOTS[who]:
        if (crop, kg) in have:
            continue
        lot = api.post("/rescue/lots", {
            "crop_code": crop, "quantity_kg": kg, "harvested_at": (now - timedelta(hours=hours_ago)).isoformat(),
            "lat": float(farm["latitude"]), "lng": float(farm["longitude"]),
            "storage_mode": "ambient", "floor_price_per_kg": 10, "temperature_c": RESCUE_TEMP_C,
        })
        step(f"{who}: Crop Rescue lot {crop} {kg} kg -> {lot.get('status')}")


def ensure_drop_address(buyer: Api) -> dict:
    items = buyer.get("/addresses", "?limit=100")["items"]
    for a in items:
        if a["address_line_1"] == DROP_ADDRESS["address_line_1"]:
            step("buyer: drop address exists")
            return a
    address = buyer.post("/addresses", DROP_ADDRESS)
    step("buyer: added the drop address (with map location) as default")
    return address


def is_demo_order(order: dict) -> bool:
    snapshot = order.get("delivery_address_snapshot") or {}
    return snapshot.get("address_line_1") == DROP_ADDRESS["address_line_1"]


def checkout(buyer: Api, listings: list[dict], address: dict, count: int) -> None:
    """Make up to `count` checkouts of LINE_KG from each listing, counting what is already sold."""
    sold = float(listings[0]["quantity"]) - float(listings[0]["available_quantity"])
    todo = count - int(sold // LINE_KG)
    if todo <= 0:
        step("buyer: the checkout was already made (stock is used), not repeating")
        return
    for n in range(todo):
        body = {
            "items": [{"listing_id": l["public_id"], "quantity": LINE_KG} for l in listings],
            "address_id": address["public_id"],
        }
        result = buyer.post("/orders", body)
        step(f"buyer: checkout {result['checkout_number']} -> {len(result['orders'])} orders")


def pay_and_confirm(buyer: Api, farmers: dict[str, Api], booker: Api) -> int:
    pending_loads = 0
    for order in buyer.get("/orders", "?limit=100"):
        if not is_demo_order(order) or order["status"] != "PLACED":
            continue
        try:
            buyer.post(f"/payments/orders/{order['public_id']}/pay-demo")
            step(f"buyer: paid order {order['order_number']} (demo money)")
        except ApiError as exc:
            print(f"  ! could not pay {order['order_number']}: {exc}")

    for who, farmer in farmers.items():
        for order in farmer.get("/orders", "?limit=100"):
            if not is_demo_order(order):
                continue
            oid = order["public_id"]
            try:
                if order["status"] == "PLACED":
                    farmer.post(f"/orders/{oid}/confirm")
                    step(f"{who}: confirmed order {order['order_number']}")
                elif order["status"] != "CONFIRMED":
                    continue
                load = booker.post(f"/logistics/orders/{oid}/request-transport")
                again = " (already booked)" if load.get("already_existed") else ""
                step(f"{booker.label}: transport for {order['order_number']} -> load {load.get('id')}{again}")
                pending_loads += 1
            except ApiError as exc:
                print(f"  ! order {order['order_number']}: {exc}")
    return pending_loads


def main() -> None:
    parser = argparse.ArgumentParser(description="Make FarmNex demo data through the public API.")
    parser.add_argument("--round", type=int, default=1, help="use a new number for a fresh demo (new listings)")
    parser.add_argument("--checkouts", type=int, default=1, help="how many checkouts of both listings (2 loads each)")
    parser.add_argument("--dry-run", action="store_true", help="only check logins and look; change nothing")
    args = parser.parse_args()

    apis = load_apis(["FARMER_1", "FARMER_2", "BUYER", "DRIVER"], optional=("MANAGER",))
    for api in apis.values():
        check_login(api)
    print(f"Logged in as {', '.join(apis)}. Server: {apis['BUYER'].base}")
    farmers = {k: apis[k] for k in ("FARMER_1", "FARMER_2")}

    vehicle = ensure_vehicle(apis["DRIVER"], args.dry_run)
    if args.dry_run:
        print("Dry run: nothing else changed.")
        return

    crop_type_id = tomato_type(apis["BUYER"])
    listings, prebids = [], []
    for who, api in farmers.items():
        farm = ensure_farm(api, who)
        batch = ensure_batch(api, who, farm, crop_type_id, args.round)
        name = who.replace("_", " ").title()
        listings.append(ensure_listing(api, who, farm, batch, f"Demo Tomatoes - {name} (R{args.round})"))
        for n in (1, 2):
            prebid = ensure_listing(api, who, farm, batch, f"Pre-harvest Tomatoes {n} - {name} (R{args.round})",
                                    listing_type="PRE_BID", quantity=PREBID_KG)
            prebids.append(ensure_bid_event(api, who, prebid))
        try:
            ensure_rescue_lots(api, who, farm)
        except ApiError as exc:
            print(f"  ! Crop Rescue lots not made for {who}: {exc}")
    # Re-read, so available_quantity is current.
    listings = [
        next(l for l in api.get("/product-listings", "?mine=true&limit=100") if l["public_id"] == lst["public_id"])
        for api, lst in zip(farmers.values(), listings)
    ]

    address = ensure_drop_address(apis["BUYER"])
    for i, event in enumerate(prebids):
        ensure_bid(apis["BUYER"], event, PRICE_PER_KG - 3 + i % 3)
    checkout(apis["BUYER"], listings, address, args.checkouts)
    booker = apis.get("MANAGER") or None
    if booker is None:
        print("(no FARMNEX_TOKEN_MANAGER: each farmer books their own transport)")
    loads = 0
    if booker is not None:
        loads = pay_and_confirm(apis["BUYER"], farmers, booker)
    else:
        for who, farmer in farmers.items():
            loads += pay_and_confirm(apis["BUYER"], {who: farmer}, farmer)
    print(f"\nDone. {loads} order(s) have a pending load near truck {vehicle['vehicle_number']}.")
    print("Next: the driver plans the trip on the phone, or run  python scripts/simulate_driver.py")


if __name__ == "__main__":
    try:
        main()
    except ApiError as exc:
        sys.exit(f"Stopped: {exc}")
