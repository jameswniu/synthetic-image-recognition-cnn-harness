"""Train the patch classifier: a ~25k-parameter CNN on 32x32 crops, exported to ONNX and int8.

Training data comes from the synthetic pages (exact labels for free) plus the four samples' page
labels, minus every crop that appears in the frozen gold set: the gold cards are the referee and
are never trained on (a tier-1 gate checks this by construction here). Deterministic: seeded, CPU.

Run: uv sync --extra train && uv run python scripts/train.py
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SYNTH = ROOT / "data" / "synth"
SAMPLES = ROOT / "data" / "samples"
LABELS = ROOT / "data" / "labels"
CARDS = ROOT / "data" / "cards" / "cards.json"
GOLD = ROOT / "data" / "gold_set.json"
MODELS = ROOT / "models"
CROP, GROW = 32, 0.25


def crop_of(gray: np.ndarray, bbox: list[int]) -> np.ndarray:
    x1, y1, x2, y2 = bbox
    gx, gy = int((x2 - x1) * GROW), int((y2 - y1) * GROW)
    a, b = max(0, y1 - gy), min(gray.shape[0], y2 + gy)
    c, d = max(0, x1 - gx), min(gray.shape[1], x2 + gx)
    crop = gray[a:b, c:d]
    if crop.size == 0:
        crop = np.full((CROP, CROP), 255, np.uint8)
    return cv2.resize(crop, (CROP, CROP), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0


def gold_keys() -> set[tuple[str, int, int]]:
    """(source, cx//8, cy//8) of every gold card, so nothing near a gold crop is trained on."""
    if not GOLD.exists():
        return set()
    keys = set()
    for c in json.loads(GOLD.read_text())["cards"]:
        if c["source"] == "synthetic":
            continue  # synthetic cards carry no page coordinates; only real crops can collide
        x1, y1, x2, y2 = c["bbox"]
        keys.add((c["source"], (x1 + x2) // 16, (y1 + y2) // 16))
    return keys


def load_dataset() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    banned = gold_keys()
    xs, ys, val_x, val_y = [], [], [], []
    # synthetic mixed pages: training. sweeps: validation.
    for split, bucket_x, bucket_y in [("mixed", xs, ys), ("sweep", val_x, val_y)]:
        for lab in sorted((SYNTH / split).glob("*.json")):
            data = json.loads(lab.read_text())
            gray = cv2.imread(str(lab.with_suffix(".png")), cv2.IMREAD_GRAYSCALE)
            for b in data["boxes"]:
                bucket_x.append(crop_of(gray, b["bbox"]))
                bucket_y.append(1.0 if b["is_checked"] else 0.0)
    # real sample crops, minus gold: training signal for the real ink distribution
    for lab in sorted(LABELS.glob("*.json")):
        data = json.loads(lab.read_text())
        gray = cv2.imread(str(SAMPLES / data["source"]), cv2.IMREAD_GRAYSCALE)
        for b in data["boxes"]:
            if b.get("ignore"):
                continue
            x1, y1, x2, y2 = b["bbox"]
            if (data["source"], (x1 + x2) // 16, (y1 + y2) // 16) in banned:
                continue
            xs.append(crop_of(gray, b["bbox"]))
            ys.append(1.0 if b["is_checked"] else 0.0)
    return (np.stack(xs)[:, None], np.array(ys, np.float32), np.stack(val_x)[:, None], np.array(val_y, np.float32))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--seed", type=int, default=13)
    args = ap.parse_args()

    import torch
    import torch.nn as nn

    torch.manual_seed(args.seed)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.use_deterministic_algorithms(True)

    x, y, vx, vy = load_dataset()
    print(f"train {len(x)} crops ({y.mean():.2%} filled), val {len(vx)} crops ({vy.mean():.2%} filled)")

    model = nn.Sequential(
        nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool2d(1),
        nn.Flatten(), nn.Linear(64, 1),
    )
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.BCEWithLogitsLoss()
    xt, yt = torch.from_numpy(x), torch.from_numpy(y)
    vxt, vyt = torch.from_numpy(vx), torch.from_numpy(vy)
    idx = np.arange(len(xt))
    rng = np.random.default_rng(args.seed)
    for epoch in range(args.epochs):
        model.train()
        rng.shuffle(idx)
        total = 0.0
        for i in range(0, len(idx), 256):
            j = idx[i : i + 256]
            opt.zero_grad()
            out = model(xt[j]).squeeze(1)
            loss = loss_fn(out, yt[j])
            loss.backward()
            opt.step()
            total += float(loss) * len(j)
        model.eval()
        with torch.no_grad():
            vp = torch.sigmoid(model(vxt).squeeze(1))
            acc = float(((vp > 0.5) == (vyt > 0.5)).float().mean())
        print(f"epoch {epoch + 1}: loss {total / len(xt):.4f} val_acc {acc:.4f}")

    MODELS.mkdir(exist_ok=True)
    fp32 = MODELS / "patch.onnx"
    torch.onnx.export(model, torch.zeros(1, 1, CROP, CROP), str(fp32), input_names=["crop"], output_names=["logit"], dynamo=False)
    from onnxruntime.quantization import QuantType, quantize_dynamic

    quantize_dynamic(str(fp32), str(MODELS / "patch-int8.onnx"), weight_type=QuantType.QInt8)

    # parity on the served artifact, scored one row at a time like serving does
    import onnxruntime as ort

    sess = ort.InferenceSession(str(MODELS / "patch-int8.onnx"), providers=["CPUExecutionProvider"])
    name = sess.get_inputs()[0].name
    preds = np.array([1 / (1 + np.exp(-sess.run(None, {name: vx[i : i + 1]})[0].ravel()[0])) for i in range(len(vx))])
    acc = float(((preds > 0.5) == (vy > 0.5)).mean())
    print(f"int8 served-artifact val_acc {acc:.4f} -> {MODELS / 'patch-int8.onnx'}")


if __name__ == "__main__":
    main()
