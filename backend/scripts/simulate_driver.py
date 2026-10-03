"""Pretend to be the driver's phone (S34) - the fallback for flaky phone GPS during the demo.

With the driver's token it: puts the truck online, plans a pooled trip from the pending loads (if there
is no trip yet), starts it, then drives to each stop sending GPS pings and marks the stop done.
Only the public /api/v2 API is used. The token is read from FARMNEX_TOKEN_DRIVER (never printed or
saved). FARMNEX_API_URL is optional (default: the production server).

Run from backend/:
  python scripts/simulate_driver.py                  # whole trip, ~3 s between pings
  python scripts/simulate_driver.py --hold-last      # stop before the LAST drop, so the buyer can watch
                                                     # the truck arrive and you finish it on the phone
  python scripts/simulate_driver.py --pings 4 --pause 2
"""

from __future__ import annotations

import argparse
import sys
import time

from seed_demo import Api, ApiError, check_login, load_apis, step


def current_or_new_trip(driver: Api, vehicle: dict) -> dict:
    vid = vehicle["id"]
    if vehicle["status"] == "offline":
        driver.call("PATCH", f"/routes/vehicles/{vid}/status", {"status": "available"})
        step("truck is online")
    trip = driver.get(f"/routes/vehicles/{vid}/current-trip")
    if trip:
        step(f"using the current trip ({trip['status']}, {len(trip['stops'])} stops)")
    else:
        trip = driver.post("/routes/trips/plan", {"vehicle_id": vid})
        step(f"planned a trip: {len(trip['stops'])} stops, {trip['total_distance_km']} km")
    if trip["status"] == "planned":
        trip = driver.post(f"/routes/trips/{trip['id']}/start")
        step("trip started")
    return trip


def drive(driver: Api, vehicle_id: str, start: tuple[float, float], stop: dict, pings: int, pause: float) -> None:
    lat0, lng0 = start
    for i in range(1, pings + 1):
        f = i / pings
        lat = lat0 + (stop["lat"] - lat0) * f
        lng = lng0 + (stop["lng"] - lng0) * f
        driver.post(f"/routes/vehicles/{vehicle_id}/location", {"lat": lat, "lng": lng, "speed_kmph": 30})
        time.sleep(pause)


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate the driver's phone for the demo.")
    parser.add_argument("--pings", type=int, default=6, help="GPS pings between two stops")
    parser.add_argument("--pause", type=float, default=3.0, help="seconds between pings")
    parser.add_argument("--hold-last", action="store_true", help="don't complete the last stop")
    args = parser.parse_args()

    driver = load_apis(["DRIVER"])["DRIVER"]
    check_login(driver)
    vehicles = driver.get("/logistics/my-vehicles")
    if not vehicles:
        sys.exit("The driver has no truck. Run scripts/seed_demo.py first.")
    vehicle = vehicles[0]
    trip = current_or_new_trip(driver, vehicle)

    position = (trip["start_lat"], trip["start_lng"])
    stops = sorted(trip["stops"], key=lambda s: s["seq"])
    for stop in stops:
        if stop["status"] == "done":
            position = (stop["lat"], stop["lng"])
            continue
        last = stop is stops[-1]
        step(f"driving to stop {stop['seq']} ({stop['kind']}): {stop['label']}")
        drive(driver, vehicle["id"], position, stop, args.pings, args.pause)
        position = (stop["lat"], stop["lng"])
        if last and args.hold_last:
            print("Holding at the last stop. Finish it on the phone (or re-run without --hold-last).")
            break
        driver.post(f"/routes/trips/{trip['id']}/stops/{stop['id']}/complete")
        step(f"stop {stop['seq']} done")
    if trip.get("tracking_url"):
        print(f"Live map: {trip['tracking_url']}")
    print("Next: the buyer taps 'Mark as received' on the order in the app (the money is then released to the farmer).")


if __name__ == "__main__":
    try:
        main()
    except ApiError as exc:
        sys.exit(f"Stopped: {exc}")
