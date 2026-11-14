#!/usr/bin/env python3
"""Held-out stress test: fresh descriptions written after the matcher was tuned, text-only (no SKU help)."""
import pandas as pd
from matcher import PartIndex, confidence, AUTO_CONF, REVIEW_FLOOR

NEW = {
 "MOT-2808": ["2808 1350Kv BLDC drone motor", "Motor, outrunner 2808"],
 "MOT-4012": ["Hi-torque 4012 motor 400 kv", "Drone motor 4012"],
 "ESC-35A": ["35A 6S ESC DShot600", "ESC 35 amp blheli"],
 "ESC-60A": ["60A ESC 12S opto", "Speed controller, 60A"],
 "PRP-10": ["10 inch carbon prop CCW", "Prop CF 10x4.5 CW"],
 "PRP-13": ["13in carbon propeller CW", "13x5.5 prop"],
 "BAT-6S-10": ["6S 10Ah Li-ion pack", "Battery 10000mAh 6S"],
 "PDB-1": ["PDB 200A", "power distribution PCB"],
 "WIR-HARN": ["Main harness assembly", "wiring harness"],
 "FC-7": ["FC-7 flight controller H7", "Flight control unit FC7"],
 "GPS-M9": ["GPS module M9N compass", "GNSS M9"],
 "RAD-L1": ["900 MHz radio module SMA connector", "Radio link SMA 900"],
 "RAD-L1B": ["900MHz radio modem U.FL", "Radio link 900 ufl"],
 "CAM-EO": ["Visible 4K camera", "EO camera module 4K"],
 "CAM-THM": ["Thermal imaging camera 640", "640 thermal module"],
 "GMB-3": ["3 axis gimbal frame", "Gimbal frame assembly"],
 "FRM-S1": ["Scout S1 carbon frame", "S1 frame"],
 "FRM-P2": ["Patrol P2 frame carbon", "P2 airframe"],
 "FRM-H3": ["H3 hauler frame", "Hauler H3 carbon fiber frame"],
 "LG-1": ["Landing gear set", "Landing gear kit"],
 "FAS-M3": ["M3x8 socket screw", "Screw M3 8mm"],
 "FAS-M4": ["M4x12 cap screw", "M4 12mm socket screw"],
 "ENC-IP65": ["IP65 enclosure dock", "Dock housing IP65"],
 "PSU-1200": ["1200W power supply", "PSU 1200 W 48V"],
 "CHG-CON": ["Charge contact spring pair", "Charging contacts pair"],
 "DCK-CTL": ["Dock controller PCB", "Dock control board"],
 "WX-SENS": ["Weather sensor", "Weather sensor module"],
}
NONPART = ["Cable ties 100pk", "Cardboard shipping box 20x20x12", "Torque wrench calibration", "Safety glasses",
           "Hand cleaner 1gal", "Label printer ribbon", "Pallet wrap roll", "Brass shims assortment"]

idx = PartIndex(pd.read_csv("data/parts_master.csv"))
rows = []
for part, ds in NEW.items():
    for d in ds:
        r = idx.score_line(d)
        rows.append((d, part, r[0][0], confidence(r[0][1], r[1][1]), r[0][1]))
for d in NONPART:
    r = idx.score_line(d)
    rows.append((d, "NONE", r[0][0], confidence(r[0][1], r[1][1]), r[0][1]))
df = pd.DataFrame(rows, columns=["text", "true", "pred", "conf", "score"])
df["status"] = df.conf.apply(lambda c: "auto" if c >= AUTO_CONF else ("review" if c >= REVIEW_FLOOR else "unmatched"))
p, n = df[df.true != "NONE"], df[df.true == "NONE"]
auto = p[p.status == "auto"]
print(f"part descriptions: {len(p)} | auto-accepted {len(auto)} ({len(auto)/len(p):.0%}) | "
      f"auto wrong: {(auto.pred != auto.true).sum()} | in review {(p.status=='review').sum()} | "
      f"unmatched {(p.status=='unmatched').sum()}")
rv = p[p.status == "review"]
print(f"review lines whose top guess is right: {(rv.pred == rv.true).sum()}/{len(rv)}")
print(f"non-part descriptions: {len(n)} | wrongly auto-accepted {(n.status=='auto').sum()} | "
      f"unmatched {(n.status=='unmatched').sum()} | review {(n.status=='review').sum()}")
print(df[(df.status == "auto") & (df.pred != df.true)][["text", "true", "pred", "conf"]].to_string())
print(df[df.status != "auto"][["text", "true", "pred", "conf", "status"]].to_string())
