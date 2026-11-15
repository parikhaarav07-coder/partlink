"""Industry packs: everything that is specific to one industry lives in packs/<id>/, not in code.

A pack folder holds:
  pack.json        labels, rule bases, wording, vocabulary (lexicon) and unit-of-measure factors
  data/            products, BOMs, parts master, suppliers, sourcing rules, spend lines (CSV, same schema for every pack)
  _answer_key/     optional hidden answer key (only exists because the demo data is synthetic)
  spec.py          optional generator spec for synthetic packs (tools/generate_pack.py)
"""
import json
import os
from dataclasses import dataclass

from core.matcher import Lexicon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKS_DIR = os.path.join(ROOT, "packs")


@dataclass
class Pack:
    id: str
    dir: str
    cfg: dict

    @property
    def name(self) -> str:
        return self.cfg["name"]

    @property
    def data_dir(self) -> str:
        return os.path.join(self.dir, "data")

    @property
    def key_path(self) -> str:
        return os.path.join(self.dir, "_answer_key", "answer_key.csv")

    @property
    def lexicon(self) -> Lexicon:
        return Lexicon.from_dict(self.cfg.get("lexicon"))

    @property
    def uom(self) -> dict:
        return {"EA": 1, **self.cfg.get("uom", {})}

    @property
    def spares_plant_prefix(self) -> str:
        return self.cfg.get("spares_plant_prefix", "MEM")

    @property
    def bases(self) -> list[str]:
        return [b["id"] for b in self.cfg["rule_bases"]]

    @property
    def basis_label(self) -> dict:
        return {b["id"]: b["label"] for b in self.cfg["rule_bases"]}

    def text(self, key: str, default: str = "") -> str:
        return self.cfg.get("text", {}).get(key, default)

    def term(self, key: str, default: str = "") -> str:
        return self.cfg.get("terms", {}).get(key, default)


def load_pack(path_or_id: str) -> Pack:
    path = path_or_id if os.path.isdir(path_or_id) else os.path.join(PACKS_DIR, path_or_id)
    with open(os.path.join(path, "pack.json")) as f:
        cfg = json.load(f)
    return Pack(id=os.path.basename(os.path.normpath(path)), dir=path, cfg=cfg)


def list_packs() -> list[Pack]:
    out = []
    for name in sorted(os.listdir(PACKS_DIR)):
        if os.path.exists(os.path.join(PACKS_DIR, name, "pack.json")):
            out.append(load_pack(name))
    out.sort(key=lambda p: p.cfg.get("order", 99))
    return out
