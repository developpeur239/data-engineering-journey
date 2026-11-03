"""Client minimal Kie.ai (images Nano Banana, clips Kling 3.0). Clé lue dans KIE_API_KEY, jamais affichée.

Chaque résultat est mis en cache (le fichier de sortie existe déjà : aucun appel, aucun crédit).
1 crédit Kie ≈ 0,005 $.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

API = "https://api.kie.ai/api/v1"
UPLOAD = "https://kieai.redpandaai.co/api/file-stream-upload"


def _h():
    return {"Authorization": f"Bearer {os.environ['KIE_API_KEY']}"}


def credits() -> float:
    r = requests.get(f"{API}/chat/credit", headers=_h(), timeout=30)
    r.raise_for_status()
    return float(r.json()["data"])


def upload(path: Path) -> str:
    """Envoie un fichier local, renvoie son URL (valable 24 h)."""
    with open(path, "rb") as f:
        r = requests.post(UPLOAD, headers=_h(), files={"file": (path.name, f)},
                          data={"uploadPath": "panne_internet", "fileName": path.name}, timeout=120)
    r.raise_for_status()
    return r.json()["data"]["downloadUrl"]


def run(model: str, inp: dict, out: Path, poll: float = 8.0, timeout: float = 1800) -> Path:
    """Crée la tâche, attend le résultat, télécharge le premier fichier. Journal dans <out>.json."""
    if out.exists():
        return out
    r = requests.post(f"{API}/jobs/createTask", headers=_h(), json={"model": model, "input": inp}, timeout=60)
    r.raise_for_status()
    body = r.json()
    if body.get("code") != 200:
        raise RuntimeError(f"Kie createTask : {body.get('code')} {body.get('msg')}")
    task = body["data"]["taskId"]
    t0 = time.time()
    while True:
        time.sleep(poll)
        d = requests.get(f"{API}/jobs/recordInfo", headers=_h(), params={"taskId": task}, timeout=60).json()["data"]
        if d["state"] == "success":
            url = json.loads(d["resultJson"])["resultUrls"][0]
            break
        if d["state"] == "fail":
            raise RuntimeError(f"Kie {model} : échec {d.get('failCode')} {d.get('failMsg')}")
        if time.time() - t0 > timeout:
            raise TimeoutError(f"Kie {model} : tâche {task} trop longue")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(requests.get(url, timeout=300).content)
    out.with_suffix(out.suffix + ".json").write_text(json.dumps(
        {"model": model, "input": inp, "taskId": task, "credits": d.get("creditsConsumed"),
         "seconds": round(time.time() - t0)}, ensure_ascii=False, indent=1))
    return out


def image(prompt: str, out: Path, refs: list[Path] = (), aspect: str = "16:9", resolution: str = "2K",
          model: str = "nano-banana-2") -> Path:
    inp = {"prompt": prompt, "image_input": [upload(p) for p in refs] if not out.exists() else [],
           "aspect_ratio": aspect, "resolution": resolution, "output_format": "png"}
    return run(model, inp, out)


def clip(prompt: str, first_frame: Path, out: Path, seconds: int = 5, mode: str = "pro") -> Path:
    """Clip Kling 3.0 à partir d'une première image, sans son (la bande-son est faite au montage)."""
    if out.exists():
        return out
    inp = {"prompt": prompt, "image_urls": [upload(first_frame)], "sound": False, "duration": str(seconds),
           "aspect_ratio": "16:9", "mode": mode, "multi_shots": False}
    return run("kling-3.0/video", inp, out)
