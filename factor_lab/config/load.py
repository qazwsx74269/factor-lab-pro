from __future__ import annotations
import yaml
from .models import AppCfg

def load_cfg(path: str) -> AppCfg:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    # backward compat: local.path -> data.local_path
    if "data" in raw and "local" in raw["data"] and isinstance(raw["data"]["local"], dict):
        raw["data"]["local_path"] = raw["data"]["local"].get("path")
    return AppCfg.model_validate(raw)
