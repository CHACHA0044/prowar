"""Seeded synthetic transaction generator for the PromptWars 2026 Fraud + AML prototype.

SYNTHETIC DATA ONLY. Every account, device, name-like ID and amount is randomly generated.

Usage:
    python generator.py                     # writes transactions.csv next to this file
    python generator.py --out data/transactions.csv --seed 42 --scale 1.0

Design:
    1. Build accounts (customers, merchants, businesses, mules, dormant mules).
    2. Generate normal behaviour (salary, rent, bills, spends, P2P, B2B).
    3. Inject benign edge cases (false-positive traps), fraud scenarios and AML scenarios.
    4. Replay all events in time order to compute running balances (no negative balances),
       resolve events that depend on earlier events (laundering hops), add retries/refunds.
    5. Write one CSV with schema columns + ground-truth labels.
"""

from __future__ import annotations

import argparse
import heapq
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- config
SEED = 42
START = datetime(2026, 10, 1)
DAYS = 45
END = START + timedelta(days=DAYS)
DIWALI_DAY = (datetime(2026, 11, 8) - START).days  # day index of the festival peak
REPORTING_THRESHOLD = 50_000.0  # structuring threshold used across the project

N_CUSTOMERS, N_MERCHANTS, N_BUSINESS, N_MULES, N_DORMANT_MULES = 1700, 200, 100, 80, 10

CITIES = {  # name: (lat, lon, weight)
    "Lucknow": (26.85, 80.95, 0.22), "Kanpur": (26.45, 80.35, 0.10), "Delhi": (28.61, 77.21, 0.13),
    "Mumbai": (19.08, 72.88, 0.10), "Bengaluru": (12.97, 77.59, 0.09), "Hyderabad": (17.39, 78.49, 0.06),
    "Chennai": (13.08, 80.27, 0.05), "Kolkata": (22.57, 88.36, 0.05), "Pune": (18.52, 73.86, 0.04),
    "Jaipur": (26.91, 75.79, 0.04), "Patna": (25.59, 85.14, 0.04), "Varanasi": (25.32, 83.00, 0.04),
    "Ahmedabad": (23.02, 72.57, 0.04),
}
CITY_NAMES = list(CITIES)
CITY_P = np.array([CITIES[c][2] for c in CITY_NAMES])

MERCHANT_COUNTS = {
    "groceries": 50, "food": 42, "fuel": 16, "shopping": 26, "travel": 10, "entertainment": 10,
    "healthcare": 12, "education": 8, "jewellery": 8, "electronics": 10, "crypto_exchange": 4, "gambling": 4,
}
SPEND_CATS = ["groceries", "food", "fuel", "shopping", "travel", "entertainment", "healthcare",
              "transfer", "atm_withdrawal", "electronics", "gambling", "crypto_exchange"]
CAT_BASE_P = np.array([.22, .20, .07, .12, .04, .07, .03, .17, .05, .01, .005, .005])
CAT_MEDIAN = np.array([520, 380, 1100, 1700, 3200, 450, 1400, 1500, 4000, 12000, 700, 4000], float)
CAT_SIGMA = np.array([.65, .6, .4, .9, 1.0, .6, .9, 1.1, .5, .8, .8, .9])
CARD_P = {"shopping": .35, "travel": .5, "electronics": .5, "gambling": .1, "crypto_exchange": .05}
ONLINE_CATS = {"shopping", "travel", "electronics", "entertainment", "gambling", "crypto_exchange"}
SEGMENT_CAT_MULT = {  # multipliers on CAT_BASE_P per segment
    "student": {"food": 1.5, "entertainment": 1.8, "fuel": .4},
    "senior": {"healthcare": 3.0, "entertainment": .4, "gambling": .1, "crypto_exchange": .1, "atm_withdrawal": 1.8},
    "self_employed": {"fuel": 1.4, "transfer": 1.3},
    "salaried": {}, "mule": {"transfer": 1.5},
}
HOUR_W = np.array([.2, .1, .07, .05, .08, .2, .8, 1.6, 2.8, 3.8, 4.6, 5, 5.2, 4.8, 4.2, 4.4, 4.8, 5.6, 6.4,
                   6.6, 6, 4.6, 2.8, 1.2])
DAY_PMF = HOUR_W / HOUR_W.sum()
NIGHT_PMF = np.roll(HOUR_W, 8) / HOUR_W.sum()
ATTACKER_DEVICES = [f"DX{i:03d}" for i in range(1, 13)]
SCENARIO_COUNTS = {
    "ato": 40, "high_value": 110, "card_testing": 42, "odd_hour": 40, "app_scam": 55, "impossible_travel": 38,
    "slow_drip": 22, "structuring": 28, "slow_structuring": 10, "smurfing": 14, "circular": 26,
    "fan_in_out": 16, "pass_through": 22, "dormant_activation": 9,
    "traveller": 40, "large_purchase": 60, "closure_drain": 10, "penny_drop": 40, "friends_cycle": 40,
    "escrow": 10, "charity": 3, "festival_share": 0.25, "phone_upgrade": 60, "one_time": 25,
    "dormant_legit": 30, "night_shift": 70, "near_threshold_rent": 15, "exact_fee": 8, "new_accounts": 40,
}


def haversine_km(a: str, b: str) -> float:
    """Great-circle distance between two configured cities."""
    la1, lo1, _ = CITIES[a]
    la2, lo2, _ = CITIES[b]
    p1, p2 = math.radians(la1), math.radians(la2)
    d = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(d))


# --------------------------------------------------------------------------- accounts
@dataclass
class Account:
    id: str
    kind: str  # customer | merchant | business | mule | dormant_mule
    city: str
    devices: list[str]
    segment: str = ""
    income: float = 0.0
    rate: float = 0.0
    merch_cat: str = ""
    created_day: int = 0
    last_day: int = DAYS - 1
    dormant_until: int = 0
    night_shift: bool = False
    one_time: bool = False
    upgrade_day: int = -1
    new_device: str = ""
    contacts: list[str] = field(default_factory=list)
    favs: dict = field(default_factory=dict)
    cat_p: np.ndarray | None = None
    employer: str = ""
    rent_amt: float = 0.0
    rent_edge: str = ""
    init_balance: float = 0.0


class Generator:
    """Builds the event list and replays it into a transactions DataFrame."""

    def __init__(self, seed: int = SEED, scale: float = 1.0):
        self.rng = np.random.default_rng(seed)
        self.scale = scale
        self.events: list[dict] = []
        self._eid = 0
        self._scn = 0
        self.accounts: dict[str, Account] = {}
        self.by_kind: dict[str, list[Account]] = {}
        self.merch_by_cat: dict[str, list[Account]] = {}
        self.merch_by_cat_city: dict[tuple, list[Account]] = {}

    # ---- small helpers -------------------------------------------------------
    def n(self, key: str) -> int:
        return max(1, int(round(SCENARIO_COUNTS[key] * self.scale)))

    def r_int(self, lo: int, hi: int) -> int:
        return int(self.rng.integers(lo, hi + 1))

    def r_u(self, lo: float, hi: float) -> float:
        return float(self.rng.uniform(lo, hi))

    def choice(self, seq):
        return seq[int(self.rng.integers(len(seq)))]

    def new_scn(self) -> str:
        self._scn += 1
        return f"SCN{self._scn:04d}"

    def when(self, day: float, hour: float = 0.0) -> datetime:
        return START + timedelta(days=int(day), hours=float(hour), seconds=self.r_int(0, 59))

    def emit(self, ts: datetime, s: str, r: str, amt: float | None = None, *, ch: str = "UPI",
             cat: str = "transfer", dev: str = "", loc: str = "", frac: float | None = None,
             ref: int | None = None, pct: float | None = None, elastic: bool = False, fraud: int = 0,
             aml: int = 0, ptype: str = "normal", scn: str = "", edge: int = 0, etype: str = "") -> int:
        """Queue one transaction event. Returns its event id, or -1 if outside the time window."""
        ts = ts.replace(microsecond=0)
        if not (START <= ts < END):
            return -1
        self._eid += 1
        self.events.append(dict(eid=self._eid, ts=ts, s=s, r=r, amt=amt, ch=ch, cat=cat, dev=dev, loc=loc,
                                frac=frac, ref=ref, pct=pct, elastic=elastic, fraud=fraud, aml=aml,
                                ptype=ptype, scn=scn, edge=edge, etype=etype))
        return self._eid

    def far_city(self, city: str, min_km: float = 600) -> str:
        far = [c for c in CITY_NAMES if haversine_km(city, c) > min_km]
        return self.choice(far)

    def merchant(self, cat: str, city: str | None = None) -> Account:
        pool = self.merch_by_cat_city.get((cat, city)) or self.merch_by_cat[cat]
        return self.choice(pool)

    def victim(self, segment: str | None = None) -> Account:
        pool = [a for a in self.established if segment is None or a.segment == segment]
        return self.choice(pool)

    # ---- account construction --------------------------------------------------
    def build_accounts(self) -> None:
        rng = self.rng
        idx = 0

        def add(kind: str, count: int, **kw) -> list[Account]:
            nonlocal idx
            made = []
            for _ in range(count):
                idx += 1
                city = CITY_NAMES[int(rng.choice(len(CITY_NAMES), p=CITY_P))]
                devs = [f"D{idx:04d}A"] + ([f"D{idx:04d}B"] if rng.random() < 0.25 else [])
                acc = Account(id=f"ACC{idx:04d}", kind=kind, city=city, devices=devs, **kw)
                self.accounts[acc.id] = acc
                self.by_kind.setdefault(kind, []).append(acc)
                made.append(acc)
            return made

        segs = rng.choice(["salaried", "student", "senior", "self_employed"], size=N_CUSTOMERS,
                          p=[.55, .12, .08, .25])
        for a, seg in zip(add("customer", N_CUSTOMERS), segs):
            a.segment = str(seg)
            med, sig, lo, hi, rate = {"salaried": (38000, .55, 12000, 250000, 1.25),
                                      "student": (8000, .3, 3000, 20000, 1.5),
                                      "senior": (22000, .4, 8000, 90000, .6),
                                      "self_employed": (55000, .7, 15000, 400000, 1.6)}[a.segment]
            a.income = float(np.clip(med * math.exp(sig * rng.standard_normal()), lo, hi))
            a.rate = rate * math.exp(.35 * rng.standard_normal())
            a.init_balance = a.income * self.r_u(.6, 3.0)

        cats = [c for c, k in MERCHANT_COUNTS.items() for _ in range(k)]
        for a, c in zip(add("merchant", N_MERCHANTS), cats):
            a.merch_cat, a.segment, a.rate = c, "merchant", .25
            a.income = 60000
            a.init_balance = self.r_u(20_000, 300_000)
            self.merch_by_cat.setdefault(c, []).append(a)
            self.merch_by_cat_city.setdefault((c, a.city), []).append(a)
        for a in add("business", N_BUSINESS):
            a.segment, a.rate, a.income = "business", 2.5, 400000
            a.init_balance = self.r_u(300_000, 3_000_000)
        for a in add("mule", N_MULES):
            a.segment, a.rate, a.income = "mule", .3, 15000
            a.init_balance = self.r_u(2_000, 40_000)
        for a in add("dormant_mule", N_DORMANT_MULES):
            a.segment = "dormant_mule"
            a.init_balance = self.r_u(500, 5_000)

        # mule rings share devices (strong graph/device signal)
        mules = self.by_kind["mule"]
        order = rng.permutation(len(mules))
        ring_id, i = 0, 0
        while i < len(order):
            size = self.r_int(3, 6)
            ring_id += 1
            for j in order[i:i + size]:
                mules[j].devices = [f"DR{ring_id:03d}"]
            i += size
        for a in self.by_kind["dormant_mule"]:
            a.devices = [f"DR{self.r_int(1, ring_id):03d}"]

        customers = self.by_kind["customer"]
        for a in customers + mules:
            pool = customers
            a.contacts = [self.choice(pool).id for _ in range(self.r_int(4, 10))]
            mult = SEGMENT_CAT_MULT.get(a.segment, {})
            p = CAT_BASE_P * np.array([mult.get(c, 1.0) for c in SPEND_CATS])
            a.cat_p = p / p.sum()
        # mules: some are brand-new accounts (cold start + suspicious)
        for a in rng.choice(mules, size=30, replace=False):
            a.created_day = self.r_int(25, 40)

        self.assign_special_roles()

    def assign_special_roles(self) -> None:
        """Mark accounts that drive benign edge cases so the generator stays deterministic and explicit."""
        rng = self.rng
        cust = self.by_kind["customer"]
        free = list(rng.permutation(len(cust)))

        def take(k: int) -> list[Account]:
            out = [cust[free.pop()] for _ in range(k)]
            return out

        for a in take(self.n("new_accounts")):
            a.created_day = self.r_int(35, 43)
            a.rate *= .8
        for a in take(self.n("one_time")):
            a.one_time = True
        for a in take(self.n("dormant_legit")):
            a.dormant_until = 36
        for a in take(self.n("night_shift")):
            a.night_shift = True
        for a in take(self.n("closure_drain")):
            a.last_day = self.r_int(38, 42)
            a.rent_edge = "closure"
        for a in take(self.n("phone_upgrade")):
            a.upgrade_day = self.r_int(10, 40)
            a.new_device = a.id.replace("ACC", "D") + "N"
        for a in take(self.n("near_threshold_rent")):
            a.income = max(a.income, self.r_u(120_000, 220_000))
            a.init_balance = a.income * 2
            a.rent_amt, a.rent_edge = 49_500.0, "near_threshold_rent"
        self.established = [a for a in cust if a.created_day == 0 and not a.one_time and a.dormant_until == 0
                            and a.rent_edge != "closure" and a.night_shift is False]

    # ---- normal behaviour --------------------------------------------------------
    def gen_fixed(self, a: Account) -> None:
        """Salary, rent, EMI, utilities and subscriptions."""
        rng, businesses = self.rng, self.by_kind["business"]
        if a.segment in ("salaried", "student", "senior", "self_employed") and a.kind == "customer":
            if a.segment == "salaried" and rng.random() < .25:
                a.employer = self.choice(businesses).id
            elif not a.employer:
                a.employer = f"EMP{self.r_int(1, 60):03d}"
            day_of_month = self.r_int(1, 5)
            cat = "pension" if a.segment == "senior" else "salary"
            for month in (10, 11):
                d = (datetime(2026, month, day_of_month) - START).days
                if a.segment == "self_employed" or d < a.created_day:
                    continue
                is_biz = a.employer.startswith("ACC")
                self.emit(self.when(d, self.r_u(9, 11)), a.employer, a.id, round(a.income * self.r_u(.98, 1.02), 2),
                          ch="NEFT", cat=cat, dev=self.accounts[a.employer].devices[0] if is_biz else "",
                          loc=self.accounts[a.employer].city if is_biz else a.city,
                          edge=int(is_biz), etype="payroll_fanout" if is_biz else "")
        if a.kind != "customer" or a.created_day > 0:
            return
        landlords = [x for x in self.by_kind["customer"] if x.segment == "self_employed" and x.id != a.id]
        if a.rent_amt or (a.segment != "senior" and rng.random() < .55):
            amt = a.rent_amt or round(a.income * self.r_u(.18, .32) / 500) * 500
            land = self.choice(landlords).id
            rd = self.r_int(1, 7)
            for month in (10, 11):
                d = (datetime(2026, month, rd) - START).days
                if d <= a.last_day:
                    self.emit(self.when(d, self.r_u(10, 20)), a.id, land, amt, ch="IMPS" if amt >= 50000 else "UPI",
                              cat="rent", dev=a.devices[0], loc=a.city, edge=int(a.rent_edge == "near_threshold_rent"),
                              etype="near_threshold_rent" if a.rent_edge == "near_threshold_rent" else "")
        if rng.random() < .35:
            emi, ed = round(a.income * self.r_u(.1, .25), 2), self.r_int(5, 12)
            biller = f"BIL{self.r_int(31, 45):03d}"
            for month in (10, 11):
                d = (datetime(2026, month, ed) - START).days
                if d <= a.last_day:
                    self.emit(self.when(d, self.r_u(6, 9)), a.id, biller, emi, ch="NACH", cat="emi", dev="", loc=a.city)
        for _ in range(self.r_int(2, 3)):
            d = self.r_int(0, DAYS - 1)
            if d <= a.last_day and d >= a.created_day:
                self.emit(self.when(d, self.r_u(8, 21)), a.id, f"BIL{self.r_int(1, 30):03d}",
                          round(self.r_u(300, 3500), 2), cat="utilities", dev=a.devices[0], loc=a.city)
        if rng.random() < .4:
            price, m = self.choice([199.0, 499.0, 649.0]), self.merchant("entertainment")
            sd = self.r_int(3, 25)
            for d in (sd, sd + 30):
                if d <= a.last_day:
                    self.emit(self.when(d, self.r_u(0, 3)), a.id, m.id, price, ch="NACH", cat="entertainment", dev="", loc="Online")

    def gen_normal(self, a: Account) -> None:
        """Poisson-rate everyday spending/P2P for one account (customers, mules)."""
        rng = self.rng
        lam = np.full(DAYS, a.rate)
        dow = (START.weekday() + np.arange(DAYS)) % 7
        lam *= np.where(dow >= 5, 1.2, 1.0)
        lam[max(0, DIWALI_DAY - 5):DIWALI_DAY + 1] *= 1.3
        lam[:a.created_day] = 0
        lam[:a.dormant_until] = 0
        lam[a.last_day + 1:] = 0
        if a.one_time:
            lam[:] = 0
        counts = rng.poisson(lam)
        total = int(counts.sum())
        first_idx = len(self.events)
        if a.one_time:
            d = self.r_int(20, 44)
            self.emit(self.when(d, self.r_u(10, 20)), a.id, self.choice(self.by_kind["customer"]).id,
                      round(self.r_u(500, 15000), 2), dev=a.devices[0], loc=a.city, edge=1, etype="one_time_account")
            return
        if total == 0:
            return
        day_idx = np.repeat(np.arange(DAYS), counts)
        hours = rng.choice(24, size=total, p=NIGHT_PMF if a.night_shift else DAY_PMF)
        secs = rng.integers(0, 3600, total)
        cat_idx = rng.choice(len(SPEND_CATS), size=total, p=a.cat_p)
        z, u, v = rng.standard_normal(total), rng.random(total), rng.random(total)
        scale = (max(a.income, 6000) / 38000) ** .45
        amounts = CAT_MEDIAN[cat_idx] * scale * np.exp(CAT_SIGMA[cat_idx] * z)
        dormant_first = a.dormant_until > 0
        for i in range(total):
            cat = SPEND_CATS[cat_idx[i]]
            day, hour = int(day_idx[i]), int(hours[i])
            ts = START + timedelta(days=day, hours=hour, seconds=int(secs[i]))
            amt = float(np.clip(amounts[i], 5, 150_000 if cat == "electronics" else 80_000))
            if cat == "atm_withdrawal":
                amt, recv, ch = max(500.0, round(amt / 500) * 500), f"ATM{self.r_int(1, 60):03d}", "ATM"
            elif cat == "transfer":
                amt = round(amt / 10) * 10.0 if v[i] < .6 else round(amt, 2)
                recv = self.choice(a.contacts) if u[i] < .88 else self.choice(self.by_kind["customer"]).id
                ch = "UPI" if (u[i] * 100 % 1) < .8 and amt < 25000 else ("IMPS" if amt < 200000 else "NEFT")
            else:
                if cat not in a.favs:
                    a.favs[cat] = [self.merchant(cat, a.city).id for _ in range(self.r_int(2, 4))]
                recv = self.choice(a.favs[cat]) if u[i] < .8 else self.merchant(cat).id
                amt = round(amt, 2)
                p_card = CARD_P.get(cat, .15)
                w = (u[i] * 997) % 1
                ch = "CARD" if w < p_card else ("WALLET" if w < p_card + .08 else "UPI")
            dev, loc = (a.new_device if (a.upgrade_day >= 0 and day >= a.upgrade_day) else self.choice(a.devices)), a.city
            if ch == "CARD":
                if cat in ONLINE_CATS and v[i] < .6:
                    loc = "Online"
                else:
                    dev = f"POS-{recv}"
            elif ch == "ATM":
                dev = recv
            if (v[i] * 991) % 1 < .02:
                loc = self.far_city(a.city, 150)  # occasional benign domestic trip noise
            edge, etype = 0, ""
            if a.night_shift and hour < 6:
                edge, etype = 1, "night_shift_worker"
            if dormant_first:
                amt, edge, etype, dormant_first = round(amt * 4, 2), 1, "dormant_reactivation", False
            self.emit(ts, a.id, recv, amt, ch=ch, cat=cat, dev=dev, loc=loc, elastic=True, edge=edge, etype=etype)
        mine = sorted(self.events[first_idx:], key=lambda e: e["ts"])
        if a.upgrade_day >= 0:
            for e in mine:
                if e["ts"] >= START + timedelta(days=a.upgrade_day):
                    e.update(edge=1, etype="device_upgrade")
                    break
        if a.created_day >= 35:
            for e in mine[:3]:
                e.update(edge=1, etype="new_account_cold_start")

    def gen_business_and_merchants(self) -> None:
        rng = self.rng
        bus, merch = self.by_kind["business"], self.by_kind["merchant"]
        for a in bus + merch:
            counts = rng.poisson(a.rate, DAYS)
            for day in range(DAYS):
                for _ in range(int(counts[day])):
                    tgt = self.choice(bus) if a.kind == "merchant" else self.choice(bus + merch)
                    if tgt.id == a.id:
                        continue
                    amt = float(np.clip(40_000 * math.exp(rng.standard_normal()), 2000, 900_000))
                    amt = round(amt, 2)
                    ch = "RTGS" if amt >= 200_000 else ("NEFT" if rng.random() < .6 else "IMPS")
                    hour = float(rng.choice(24, p=DAY_PMF)) + self.r_u(0, .99)
                    self.emit(self.when(day, hour), a.id, tgt.id, amt, ch=ch, cat="wholesale", dev=a.devices[0],
                              loc=a.city, elastic=True)

    # ---- benign edge cases -----------------------------------------------------------
    def edge_cases(self) -> None:
        rng = self.rng
        cust = self.established
        E = dict(edge=1)
        # travellers: new city (+ sometimes new device), travel-heavy spending
        for a in rng.choice(cust, self.n("traveller"), replace=False):
            d0, length, city = self.r_int(5, 38), self.r_int(3, 6), self.far_city(a.city, 400)
            dev = f"DT{a.id[3:]}" if rng.random() < .4 else a.devices[0]
            for _ in range(self.r_int(6, 15)):
                cat = self.choice(["travel", "food", "shopping", "atm_withdrawal", "food", "entertainment"])
                m = self.merchant(cat, city) if cat != "atm_withdrawal" else None
                amt = round(float(CAT_MEDIAN[SPEND_CATS.index(cat)]) * 2 * math.exp(.6 * rng.standard_normal()), 2)
                self.emit(self.when(d0 + self.r_int(0, length), self.r_u(7, 23)), a.id,
                          m.id if m else f"ATM{self.r_int(1, 60):03d}", amt if cat != "atm_withdrawal" else 5000.0,
                          ch="ATM" if m is None else self.choice(["CARD", "UPI"]), cat=cat, dev=dev, loc=city,
                          elastic=True, etype="traveller_new_location", **E)
        # large legitimate one-off purchases
        for a in rng.choice(cust, self.n("large_purchase"), replace=False):
            cat = self.choice(["jewellery", "electronics", "travel"])
            m = self.merchant(cat, a.city)
            self.emit(self.when(self.r_int(6, 43), self.r_u(11, 19)), a.id, m.id, None, ch=self.choice(["CARD", "NEFT"]),
                      cat=cat, dev=f"POS-{m.id}", loc=a.city, frac=self.r_u(.4, .7), etype="large_legit_purchase", **E)
        # account closure: full-balance sweep to the holder's other account
        for a in [x for x in self.by_kind["customer"] if x.rent_edge == "closure"]:
            other = self.choice(self.established)
            self.emit(self.when(a.last_day, self.r_u(12, 18)) + timedelta(hours=1), a.id, other.id, None, ch="NEFT",
                      dev=a.devices[0], loc=a.city, frac=1.0, etype="account_closure_drain", **E)
        # penny-drop beneficiary verification
        for a in rng.choice(cust, self.n("penny_drop"), replace=False):
            tgt, t = self.choice(cust), self.when(self.r_int(3, 43), self.r_u(10, 19))
            self.emit(t, a.id, tgt.id, 1.0, dev=a.devices[0], loc=a.city, etype="penny_drop_verification", **E)
            self.emit(t + timedelta(minutes=self.r_u(2, 10)), a.id, tgt.id, round(self.r_u(5000, 30000) / 100) * 100,
                      dev=a.devices[0], loc=a.city, elastic=True, etype="penny_drop_verification", **E)
        # roommates settling small bills in a loop (benign cycle)
        for _ in range(self.n("friends_cycle")):
            a = self.choice(cust)
            mates = [x for x in cust if x.city == a.city and x.id != a.id]
            trio = [a] + [self.choice(mates) for _ in range(2)]
            if len({x.id for x in trio}) < 3:
                continue
            t = self.when(self.r_int(3, 43), self.r_u(9, 20))
            for i, x in enumerate(trio):
                y = trio[(i + 1) % 3]
                self.emit(t + timedelta(minutes=45 * i), x.id, y.id, float(self.r_int(3, 20) * 100), dev=x.devices[0],
                          loc=x.city, elastic=True, etype="friends_settlement_cycle", **E)
        # escrow/broker: large inbound forwarded after 1-3 days (slow, benign)
        brokers = self.by_kind["business"]
        for b in rng.choice(brokers, self.n("escrow"), replace=False):
            buyer, seller = self.choice(cust), self.choice(cust)
            t = self.when(self.r_int(3, 38), self.r_u(10, 16))
            amt = round(self.r_u(500_000, 1_000_000), -3)
            e1 = self.emit(t, buyer.id, b.id, amt, ch="RTGS", cat="property_escrow", dev=buyer.devices[0], loc=buyer.city, etype="escrow_pass_through", **E)
            self.emit(t + timedelta(days=self.r_u(1, 3)), b.id, seller.id, None, ch="RTGS", cat="property_escrow",
                      dev=b.devices[0], loc=b.city, ref=e1, pct=.995, etype="escrow_pass_through", **E)
        # charity fundraiser: benign one-day fan-in
        for _ in range(self.n("charity")):
            trust, day = self.choice(brokers), self.r_int(10, 40)
            for donor in rng.choice(self.by_kind["customer"], self.r_int(150, 300), replace=False):
                self.emit(self.when(day, float(rng.choice(24, p=DAY_PMF)) + self.r_u(0, .99)), donor.id, trust.id,
                          float(round(float(np.clip(800 * math.exp(rng.standard_normal()), 100, 5000)) / 10) * 10),
                          cat="donation", dev=donor.devices[0], loc=donor.city, elastic=True, etype="charity_fan_in", **E)
        # Diwali spike: extra shopping on festival days
        for a in rng.choice(cust, int(len(cust) * SCENARIO_COUNTS["festival_share"]), replace=False):
            for _ in range(self.r_int(2, 5)):
                cat = self.choice(["shopping", "jewellery", "electronics", "travel", "food"])
                m = self.merchant(cat, a.city)
                amt = round(float(CAT_MEDIAN[SPEND_CATS.index(cat) if cat in SPEND_CATS else 3]) * 1.6 *
                            math.exp(.9 * rng.standard_normal()), 2)
                self.emit(self.when(DIWALI_DAY - self.r_int(0, 4), self.r_u(10, 21)), a.id, m.id, amt, ch=self.choice(["CARD", "UPI"]),
                          cat=cat, dev=a.devices[0], loc=a.city, elastic=True, etype="festival_spike", **E)
        # exact-threshold tuition fee (legit)
        for a in rng.choice(cust, self.n("exact_fee"), replace=False):
            m = self.merchant("education")
            self.emit(self.when(self.r_int(5, 30), self.r_u(10, 16)), a.id, m.id, REPORTING_THRESHOLD, ch="NEFT",
                      cat="education", dev=a.devices[0], loc=a.city, etype="exact_threshold_fee", **E)

    # ---- fraud scenarios --------------------------------------------------------------
    def launder(self, ref: int, mule: Account, t: datetime, sid: str, hops: int) -> None:
        """Mule forwards received funds onward; hops depend on the earlier transaction's resolved amount."""
        cur = mule
        for _ in range(hops):
            nxt = self.choice([m for m in self.by_kind["mule"] if m.id != cur.id])
            t += timedelta(minutes=self.r_u(2, 25))
            ref = self.emit(t, cur.id, nxt.id, None, ch="IMPS", dev=cur.devices[0], loc=cur.city, ref=ref,
                            pct=self.r_u(.93, .99), aml=1, ptype="pass_through", scn=sid)
            cur = nxt

    def scn_ato(self) -> None:
        v, sid = self.victim(), self.new_scn()
        dev, far = self.choice(ATTACKER_DEVICES), self.far_city(v.city)
        t = self.when(self.r_int(8, DAYS - 2), self.choice([0, 1, 2, 3, 4, 23, 14, 16]) + self.r_u(0, .9))
        mule = self.choice(self.by_kind["mule"])
        for i in range(self.r_int(3, 8)):
            t += timedelta(minutes=self.r_u(1, 9))
            m = mule if i < 2 else self.choice(self.by_kind["mule"])
            e = self.emit(t, v.id, m.id, None, ch=self.choice(["IMPS", "UPI", "NEFT"]), dev=dev, loc=far,
                          frac=self.r_u(.3, .65), fraud=1, ptype="account_takeover", scn=sid)
            if e > 0 and self.rng.random() < .7:
                self.launder(e, m, t, sid, self.r_int(1, 2))

    def scn_high_value(self) -> None:
        v, sid = self.victim(), self.new_scn()
        new_dev = self.rng.random() < .5
        tgt = self.choice(self.by_kind["mule"] + self.by_kind["customer"])
        t = self.when(self.r_int(8, DAYS - 1), float(self.rng.choice(24, p=DAY_PMF)) + self.r_u(0, .99))
        self.emit(t, v.id, tgt.id, None, ch=self.choice(["NEFT", "IMPS", "UPI"]),
                  dev=self.choice(ATTACKER_DEVICES) if new_dev else v.devices[0],
                  loc=self.far_city(v.city) if new_dev else v.city, frac=self.r_u(.5, .9), fraud=1,
                  ptype="high_value_anomaly", scn=sid)

    def scn_card_testing(self) -> None:
        v, sid = self.victim(), self.new_scn()
        dev, t = self.choice(ATTACKER_DEVICES), self.when(self.r_int(8, DAYS - 1), self.r_u(0, 23))
        for i in range(self.r_int(10, 25)):
            t += timedelta(seconds=self.r_u(8, 60))
            cat = self.choice(["electronics", "shopping", "entertainment", "travel", "gambling"])
            amt = round(self.r_u(1, 10), 2) if i < 3 else round(self.r_u(50, 2500), 2)
            self.emit(t, v.id, self.merchant(cat).id, amt, ch="CARD", cat=cat, dev=dev, loc="Online", fraud=1,
                      ptype="card_testing", scn=sid)
        if self.rng.random() < .7:
            t += timedelta(minutes=self.r_u(1, 5))
            self.emit(t, v.id, self.merchant("electronics").id, round(self.r_u(8000, 45000), 2), ch="CARD",
                      cat="electronics", dev=dev, loc="Online", fraud=1, ptype="card_testing", scn=sid)

    def scn_odd_hour(self) -> None:
        v, sid = self.victim(), self.new_scn()
        new_dev = self.rng.random() < .6
        t = self.when(self.r_int(8, DAYS - 1), self.r_u(1, 4))
        for _ in range(self.r_int(3, 6)):
            t += timedelta(minutes=self.r_u(10, 30))
            cat = self.choice(["gambling", "crypto_exchange", "electronics", "jewellery"])
            self.emit(t, v.id, self.merchant(cat).id, None, ch=self.choice(["UPI", "CARD"]), cat=cat,
                      dev=self.choice(ATTACKER_DEVICES) if new_dev else v.devices[0],
                      loc=self.far_city(v.city) if new_dev else v.city, frac=self.r_u(.2, .45), fraud=1,
                      ptype="odd_hour_spike", scn=sid)

    def scn_app_scam(self) -> None:
        """Authorised push payment: victim's own device and city, so only behaviour gives it away."""
        seniors = self.rng.random() < .6
        v, sid = self.victim("senior" if seniors else None), self.new_scn()
        mule = self.choice(self.by_kind["mule"])
        t = self.when(self.r_int(8, DAYS - 1), self.r_u(10, 17))
        for i in range(self.r_int(1, 3)):
            e = self.emit(t, v.id, mule.id, None, ch=self.choice(["UPI", "IMPS"]), dev=v.devices[0], loc=v.city,
                          frac=self.r_u(.5, .85), fraud=1, ptype="app_scam", scn=sid)
            if e > 0 and i == 0 and self.rng.random() < .8:
                self.launder(e, mule, t, sid, self.r_int(1, 3))
            t += timedelta(minutes=self.r_u(20, 90))

    def scn_impossible_travel(self) -> None:
        v, sid = self.victim(), self.new_scn()
        far = self.far_city(v.city, 1000)
        t = self.when(self.r_int(8, DAYS - 1), self.r_u(10, 20))
        m = self.merchant("shopping", v.city)
        self.emit(t, v.id, m.id, round(self.r_u(300, 4000), 2), ch="CARD", cat="shopping", dev=f"POS-{m.id}",
                  loc=v.city, scn=sid)  # legitimate anchor in the home city
        for _ in range(self.r_int(2, 3)):
            t += timedelta(minutes=self.r_u(5, 20))
            cat = self.choice(["electronics", "jewellery", "atm_withdrawal"])
            if cat == "atm_withdrawal":
                r, dev, amt = f"ATM{self.r_int(1, 60):03d}", None, round(self.r_u(10000, 40000) / 500) * 500.0
                dev = r
            else:
                mm = self.merchant(cat, far)
                r, dev, amt = mm.id, f"POS-{mm.id}", round(self.r_u(8000, 60000), 2)
            self.emit(t, v.id, r, amt, ch="ATM" if cat == "atm_withdrawal" else "CARD", cat=cat, dev=dev, loc=far,
                      fraud=1, ptype="impossible_travel", scn=sid)

    def scn_slow_drip(self) -> None:
        v, sid = self.victim(), self.new_scn()
        mule, d = self.choice(self.by_kind["mule"]), self.r_int(6, 20)
        for _ in range(self.r_int(6, 12)):
            self.emit(self.when(d, self.r_u(10, 20)), v.id, mule.id, round(self.r_u(900, 2400) / 10) * 10.0,
                      dev=v.devices[0], loc=v.city, fraud=1, ptype="slow_drip", scn=sid)
            d += self.r_u(1, 2.5)

    # ---- AML scenarios -------------------------------------------------------------------
    def _near_threshold(self) -> float:
        if self.rng.random() < .5:
            return self.choice([49900.0, 49500.0, 49000.0, 48500.0, 49999.0])
        return round(self.r_u(45000, 49999) / 100) * 100.0

    def scn_structuring(self, slow: bool = False) -> None:
        pool = [a for a in self.established if a.segment in ("self_employed", "salaried")]
        s, sid = self.choice(pool), self.new_scn()
        recvs = [self.choice(self.by_kind["mule"] + self.by_kind["customer"]) for _ in range(self.r_int(1, 3))]
        n = self.r_int(8, 12) if slow else self.r_int(6, 14)
        t0 = self.when(self.r_int(6, DAYS - 8), self.r_u(9, 14))
        span = timedelta(days=self.r_u(3, 6)) if slow else timedelta(hours=self.r_u(1, 6))
        for off in sorted(self.rng.random(n)):
            self.emit(t0 + span * float(off), s.id, self.choice(recvs).id, self._near_threshold(),
                      ch=self.choice(["IMPS", "UPI", "NEFT"]), dev=s.devices[0], loc=s.city, aml=1,
                      ptype="structuring", scn=sid)

    def scn_smurfing(self) -> None:
        sid, collector = self.new_scn(), self.choice(self.by_kind["mule"])
        t0 = self.when(self.r_int(6, DAYS - 4), self.r_u(8, 14))
        senders = self.by_kind["customer"] + self.by_kind["mule"]
        for _ in range(self.r_int(8, 16)):
            s = self.choice(senders)
            for _ in range(self.r_int(1, 2)):
                self.emit(t0 + timedelta(hours=self.r_u(0, 40)), s.id, collector.id, round(self.r_u(44000, 49999) / 100) * 100.0,
                          ch=self.choice(["IMPS", "UPI"]), dev=s.devices[0], loc=s.city, aml=1, ptype="smurfing", scn=sid)

    def scn_circular(self) -> None:
        sid, length = self.new_scn(), self.r_int(3, 6)
        mules = self.by_kind["mule"]
        ring = [mules[i] for i in self.rng.choice(len(mules), length, replace=False)]
        if self.rng.random() < .5:
            ring[0] = self.choice(self.established)
        amt, t = round(self.r_u(250_000, 900_000), -2), self.when(self.r_int(5, DAYS - 6), self.r_u(8, 16))
        loops = int(self.rng.choice([1, 2, 3], p=[.6, .3, .1]))
        for _ in range(loops):
            for i, a in enumerate(ring):
                b = ring[(i + 1) % length]
                self.emit(t, a.id, b.id, round(amt, 2), ch="RTGS" if amt >= 200_000 else "IMPS", dev=a.devices[0],
                          loc=a.city, aml=1, ptype="circular_flow", scn=sid)
                amt *= self.r_u(.98, .995)
                t += timedelta(hours=self.r_u(.1, 6))
            t += timedelta(hours=self.r_u(6, 30))

    def scn_fan_in_out(self) -> None:
        sid, hub = self.new_scn(), self.choice(self.by_kind["mule"])
        t0, total = self.when(self.r_int(6, DAYS - 5), self.r_u(8, 12)), 0.0
        senders = self.by_kind["customer"]
        for _ in range(self.r_int(10, 30)):
            s, amt = self.choice(senders), round(self.r_u(3000, 45000), 2)
            self.emit(t0 + timedelta(hours=self.r_u(0, 30)), s.id, hub.id, amt, dev=s.devices[0], loc=s.city,
                      aml=1, ptype="fan_in", scn=sid)
            total += amt
        k = self.r_int(5, 15)
        shares = self.rng.dirichlet(np.ones(k))
        t_out = t0 + timedelta(hours=32)
        for share in shares:
            tgt = self.choice(self.by_kind["mule"] + self.by_kind["customer"])
            self.emit(t_out + timedelta(minutes=self.r_u(0, 120)), hub.id, tgt.id, round(total * .95 * float(share), 2),
                      ch="IMPS", dev=hub.devices[0], loc=hub.city, aml=1, ptype="fan_out", scn=sid)

    def scn_pass_through(self) -> None:
        sid, mules = self.new_scn(), self.by_kind["mule"]
        src = self.choice(self.by_kind["business"] + mules)
        chain = [mules[i] for i in self.rng.choice(len(mules), self.r_int(3, 5), replace=False)]
        t = self.when(self.r_int(5, DAYS - 3), self.r_u(9, 20))
        ref = self.emit(t, src.id, chain[0].id, round(self.r_u(150_000, 800_000), -2), ch="RTGS", dev=src.devices[0],
                        loc=src.city, aml=1, ptype="pass_through", scn=sid)
        for a, b in zip(chain, chain[1:]):
            t += timedelta(minutes=self.r_u(2, 15))
            ref = self.emit(t, a.id, b.id, None, ch="IMPS", dev=a.devices[0], loc=a.city, ref=ref, pct=self.r_u(.95, .99),
                            aml=1, ptype="pass_through", scn=sid)
        if self.rng.random() < .4:
            cat = self.choice(["crypto_exchange", "gambling"])
            t += timedelta(minutes=self.r_u(2, 15))
            self.emit(t, chain[-1].id, self.merchant(cat).id, None, ch="IMPS", cat=cat, dev=chain[-1].devices[0],
                      loc=chain[-1].city, ref=ref, pct=.97, aml=1, ptype="pass_through", scn=sid)

    def scn_dormant_activation(self, dormant: Account) -> None:
        sid, t = self.new_scn(), self.when(self.r_int(18, 40), self.r_u(9, 15))
        total = 0.0
        for _ in range(self.r_int(2, 4)):
            src = self.choice(self.by_kind["customer"] + self.by_kind["mule"])
            amt = round(self.r_u(100_000, 300_000), -2)
            self.emit(t, src.id, dormant.id, amt, ch="RTGS", dev=src.devices[0], loc=src.city, aml=1,
                      ptype="dormant_activation", scn=sid)
            total += amt
            t += timedelta(minutes=self.r_u(5, 20))
        t += timedelta(minutes=self.r_u(30, 90))
        for share in self.rng.dirichlet(np.ones(self.r_int(2, 4))):
            tgt = self.choice(self.by_kind["mule"])
            self.emit(t, dormant.id, tgt.id, round(total * .96 * float(share), 2), ch="IMPS", dev=dormant.devices[0],
                      loc=dormant.city, aml=1, ptype="dormant_activation", scn=sid)
            t += timedelta(minutes=self.r_u(2, 25))

    # ---- replay -----------------------------------------------------------------------------
    def finalize(self) -> pd.DataFrame:
        """Replay events chronologically: balances, dependent amounts, retries and refunds."""
        rng = self.rng
        bal = {a.id: a.init_balance for a in self.accounts.values()}
        heap = [(e["ts"], e["eid"], e) for e in self.events]
        heapq.heapify(heap)
        resolved: dict[int, float] = {}
        rows: list[dict] = []
        derived_eid = self._eid
        while heap:
            _, _, e = heapq.heappop(heap)
            s, b, amt = e["s"], bal.get(e["s"]), e["amt"]
            if e["ref"] is not None:
                base = resolved.get(e["ref"])
                if base is None:
                    continue
                amt = round(base * e["pct"], 2)
            elif e["frac"] is not None:
                if b is None or b < 1500:
                    continue
                amt = round(b * e["frac"], 2)
            if amt is None or amt <= 0:
                continue
            if b is not None:
                if e["elastic"]:
                    amt = min(amt, round(b * .85, 2))
                    if amt < 10 and e["etype"] != "penny_drop_verification":
                        continue
                elif amt > b:
                    b = round(amt * float(rng.uniform(1.02, 1.5)), 2)  # notional unlogged funding (e.g. cash)
            resolved[e["eid"]] = amt
            dev, loc, edge, etype = e["dev"], e["loc"], e["edge"], e["etype"]
            if e["ptype"] == "normal" and not edge and rng.random() < .003:
                if rng.random() < .5:
                    dev = ""
                else:
                    loc = ""
                edge, etype = 1, "missing_metadata"
            rows.append(dict(timestamp=e["ts"], sender_id=s, receiver_id=e["r"], amount=amt, channel=e["ch"],
                             merchant_category=e["cat"], device_id=dev, location=loc,
                             sender_balance_before=round(b, 2) if b is not None else np.nan,
                             is_fraud=e["fraud"], is_aml_pattern=e["aml"], pattern_type=e["ptype"],
                             scenario_id=e["scn"], is_edge_case=edge, edge_case_type=etype))
            if b is not None:
                bal[s] = round(b - amt, 2)
            if e["r"] in bal:
                bal[e["r"]] = round(bal[e["r"]] + amt, 2)
            # benign derived events: gateway retry duplicates and merchant refunds
            if e["ptype"] == "normal" and not edge and b is not None and e["ch"] in ("UPI", "CARD"):
                x = rng.random()
                if x < .0015:
                    derived_eid += 1
                    d = dict(e, eid=derived_eid, ts=e["ts"] + timedelta(seconds=int(rng.integers(1, 5))), amt=amt,
                             frac=None, ref=None, elastic=False, edge=1, etype="duplicate_retry")
                    heapq.heappush(heap, (d["ts"], d["eid"], d))
                elif x < .0022 and e["r"] in self.accounts and self.accounts[e["r"]].kind == "merchant":
                    derived_eid += 1
                    d = dict(e, eid=derived_eid, ts=e["ts"] + timedelta(hours=float(rng.uniform(1, 40))), s=e["r"],
                             r=s, amt=amt, frac=None, ref=None, elastic=False, cat="refund", edge=1,
                             etype="refund_reversal", dev=self.accounts[e["r"]].devices[0])
                    heapq.heappush(heap, (d["ts"], d["eid"], d))
        df = pd.DataFrame(rows)
        df = df[(df.timestamp >= START) & (df.timestamp < END)]
        df = df.sort_values("timestamp", kind="stable").reset_index(drop=True)
        df.insert(0, "txn_id", [f"T{i + 1:06d}" for i in range(len(df))])
        df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")
        return df

    def run(self) -> pd.DataFrame:
        self.build_accounts()
        for a in self.by_kind["customer"] + self.by_kind["mule"]:
            self.gen_fixed(a)
            self.gen_normal(a)
        self.gen_business_and_merchants()
        self.edge_cases()
        for name, fn in [("ato", self.scn_ato), ("high_value", self.scn_high_value),
                         ("card_testing", self.scn_card_testing), ("odd_hour", self.scn_odd_hour),
                         ("app_scam", self.scn_app_scam), ("impossible_travel", self.scn_impossible_travel),
                         ("slow_drip", self.scn_slow_drip), ("structuring", self.scn_structuring),
                         ("smurfing", self.scn_smurfing), ("circular", self.scn_circular),
                         ("fan_in_out", self.scn_fan_in_out), ("pass_through", self.scn_pass_through)]:
            for _ in range(self.n(name)):
                fn()
        for _ in range(self.n("slow_structuring")):
            self.scn_structuring(slow=True)
        dormant = self.by_kind["dormant_mule"]
        for a in dormant[:min(len(dormant), self.n("dormant_activation"))]:
            self.scn_dormant_activation(a)
        return self.finalize()


# --------------------------------------------------------------------------- validation
def validate(df: pd.DataFrame) -> dict:
    """Sanity checks on labels and structure. Raises AssertionError on a broken dataset."""
    ts = pd.to_datetime(df["timestamp"])
    assert ts.is_monotonic_increasing, "rows must be time-ordered"
    assert df["txn_id"].is_unique and (df["amount"] > 0).all()
    known = df["sender_balance_before"].notna()
    assert (df.loc[known, "sender_balance_before"] + 0.01 >= df.loc[known, "amount"]).all(), "overdraft"
    fraud_rate = df["is_fraud"].mean()
    assert .01 <= fraud_rate <= .03, f"fraud rate {fraud_rate:.3%} outside 1-3%"
    near = df[(df.amount >= 45_000) & (df.amount < REPORTING_THRESHOLD)]
    struct = df[df.pattern_type == "structuring"]
    assert (struct.amount.between(45_000, REPORTING_THRESHOLD - 1)).all()
    circ = df[df.pattern_type == "circular_flow"]
    for sid, g in circ.groupby("scenario_id"):
        assert set(g.sender_id) == set(g.receiver_id), f"{sid}: cycle not closed"
    return dict(rows=len(df), fraud_rate=round(float(fraud_rate), 4), aml_rate=round(float(df.is_aml_pattern.mean()), 4),
                near_threshold_rows=len(near), accounts=len(set(df.sender_id) | set(df.receiver_id)))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", default=str(Path(__file__).with_name("transactions.csv")))
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--scale", type=float, default=1.0, help="multiplies scenario counts")
    args = p.parse_args()
    df = Generator(args.seed, args.scale).run()
    summary = validate(df)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(summary)
    print(df.pattern_type.value_counts().to_string())
    print(df[df.is_edge_case == 1].edge_case_type.value_counts().to_string())


if __name__ == "__main__":
    main()
