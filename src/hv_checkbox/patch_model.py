"""Optional learned second reader: a tiny CNN over 32x32 box crops, served as ONNX int8.

The deterministic rules stay primary. When the model file exists, its read is compared with the
rule's; agreement raises confidence, disagreement lowers it and tags CLASSIFIER_DISAGREE, and the
final is_checked always comes from the deterministic side, so behavior without the file is a strict
subset. onnxruntime (and onnx, same optional extra) is imported lazily: the default install and the
Docker image run rule-only.
"""

from __future__ import annotations

import copy
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import SimpleQueue

import cv2
import numpy as np

from hv_checkbox.normalize import Page
from hv_checkbox.types import Box

MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "models" / "patch-int8.onnx"
CROP = 32
GROW = 0.25

# How one page's crops get scored, and why it looks the way it does. Three arrangements were
# measured before this one and each taught the constraint the next had to respect:
#   1. A plain per-crop session.run loop: honest p50 6.7-8.1 ms/page. The per-crop Python/C++
#      round trip is the fixed cost; intra-op threading inside one tiny 1x1x32x32 Run only slows
#      it down (83 -> 55 us/crop measured going to intra_op=1, logits bitwise identical).
#   2. The same unmodified single-crop session run concurrently from a small thread pool, one
#      task per contiguous chunk of crops (per-crop tasks pay the queue hop ~118x a page):
#      honest p50 3.6-4.0 ms/page. Real, but it plateaus at ~3x on 6 workers because every crop
#      still needs the GIL ~2x for its Python wrapper, ~236 GIL acquisitions per page.
#   3. Two "obvious" improvements on top of 2 are measured LOSSES on a GIL build (same-load
#      controls): moving extract_crop into the workers (4.0 -> 5.7 ms) and starting scoring
#      before the classify rules pass to overlap the two (4.0 -> 6.4-7.0 ms, the classify loop
#      itself stretching ~1.8 -> ~9 ms). Any scheme that adds per-crop GIL demand to a window
#      where another thread needs the interpreter loses more to the convoy than it hides. (The
#      overlap is byte-safe, classify writes only state fields while the scorer reads only
#      gray + geometry, so it may become worthwhile on a free-threaded build; not on this one.)
# What ships below: each pool task makes ONE onnxruntime Run over its whole chunk, using the
# SAME per-crop graph wrapped in an ONNX Scan node built in memory at init (see __init__; the
# construction is recorded and testable in make_dynamic_batch.py, and models/patch-int8.onnx is
# never modified). Scan's per-iteration dispatch costs about what the Python loop cost
# (~55-68 us/crop single-threaded, measured), so ONE thread gains nothing, which is why the
# earlier note called it a dead end. What it changes is WHERE the time is spent: the whole chunk
# runs inside a single GIL-released Run, cutting the drain's GIL demand from ~236 acquisitions a
# page to a handful, so the workers actually run wide and the main thread can keep extracting
# the next chunk while they do. One trap made the first cut of this SLOWER than the pool it
# replaced: concurrent Run() calls on a single session whose graph contains a Scan SERIALIZE
# inside onnxruntime (measured 1.00x scale from 6 threads; plain single-crop sessions do not do
# this), so each worker gets its OWN session, all built from the same in-memory bytes. That
# restores real concurrency (4.25x measured on the same probe) at the cost of duplicating a
# 29 KB model per worker. Quantization semantics are untouched throughout: each Scan iteration
# feeds one crop through the four DynamicQuantizeLinear nodes exactly as the loop did (bitwise
# identical, 0.0 max abs diff, re-verified on the real corpus; the naive alternative, relabeling
# the batch dim, pools quantization statistics across crops and drifts ~2.5e-3).
POOL_WORKERS = max(1, min(6, os.cpu_count() or 1))

# Chunk sizes taper geometrically. The page's wall time is max over chunks of
# (time until that chunk is extracted and submitted) + (its own scan time), so equal chunks make
# the LAST one the straggler: it cannot start before all extraction is done and then costs a full
# chunk-scan on top. Tapering by roughly 1 - extract_rate/scan_rate keeps
# submit_time + scan_time roughly constant across chunks; extraction measures ~12.7 us/crop and
# a Scan iteration ~90-95 us/crop when several workers run at once (memory contention lifts it
# from the ~68 us single-thread number), giving ~0.86. The floor of 8 stops the tail
# degenerating into many tiny Runs: each submit costs the MAIN thread a queue hop, and with the
# drain measured at ~0.3 ms the tail chunks were pure overhead at 4.
_TAPER = 0.86
_MIN_CHUNK = 8


def _schedule(n: int) -> list[int]:
    """Tapered chunk sizes summing to n (empty for n=0); first ~n/4.5, floor of _MIN_CHUNK."""
    sizes: list[int] = []
    step = n * (1 - _TAPER)
    rem = n
    while rem > 0:
        s = min(rem, max(_MIN_CHUNK, round(step)))
        sizes.append(s)
        rem -= s
        step *= _TAPER
    return sizes


def _crop_u8(gray: np.ndarray, box: Box) -> np.ndarray:
    """The geometry-and-resize half of extract_crop: the grown window resized to CROPxCROP,
    still uint8. Split out so score() can run exactly this on the main thread and leave the
    (byte-identical, see _scan_logits) float conversion to the pool."""
    gx, gy = int(box.w * GROW), int(box.h * GROW)
    x1, y1 = max(0, box.x1 - gx), max(0, box.y1 - gy)
    x2, y2 = min(gray.shape[1], box.x2 + gx), min(gray.shape[0], box.y2 + gy)
    crop = gray[y1:y2, x1:x2]
    if crop.size == 0:
        crop = np.full((CROP, CROP), 255, np.uint8)
    return cv2.resize(crop, (CROP, CROP), interpolation=cv2.INTER_AREA)


def extract_crop(gray: np.ndarray, box: Box) -> np.ndarray:
    return (_crop_u8(gray, box).astype(np.float32) / 255.0)[None, :, :]  # 1xHxW


class PatchScorer:
    def __init__(self, path: Path = MODEL_PATH):
        import onnx
        import onnxruntime as ort  # lazy: only when a model is actually used
        from onnx import TensorProto, helper

        opts = ort.SessionOptions()
        # intra_op=1 on BOTH sessions. For the single-crop reference session the reason is the
        # measured 83 -> 55 us/crop above. For the Scan session it is also what makes concurrent
        # Run() calls from several pool workers compose: each Run executes entirely on the thread
        # that called it instead of fighting over a shared intra-op pool.
        opts.intra_op_num_threads = 1

        # The reference session: the unmodified per-crop graph, exactly as trained and shipped.
        # score() does not call it; it exists so the ground truth the Scan path must match stays
        # loadable and checkable in place (the bitwise harness compares against this session).
        self.session = ort.InferenceSession(str(path), sess_options=opts, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

        # The serving graph: the SAME node list, byte-untouched, as the body of a Scan over a
        # new leading axis, built in memory here every init (deterministic; nothing written to
        # models/). Input [N,1,1,32,32]; each iteration slices off the N and hands the body the
        # [1,1,32,32] it always expected, initializers visible from the outer scope, so no weight
        # is duplicated or altered in the GRAPH; the per-worker session copies below are a
        # runtime memory trade, not a model change.
        model = onnx.load(str(path))
        g = model.graph
        body = helper.make_graph(
            nodes=[copy.deepcopy(n) for n in g.node],
            name="patch_body",
            inputs=[helper.make_tensor_value_info(g.input[0].name, TensorProto.FLOAT, [1, 1, 32, 32])],
            outputs=[helper.make_tensor_value_info(g.output[0].name, TensorProto.FLOAT, [1, 1])],
            initializer=[],
        )
        scan = helper.make_node("Scan", inputs=["crops"], outputs=["logits"], body=body, num_scan_inputs=1)
        outer = helper.make_graph(
            nodes=[scan],
            name=g.name + "_scanchunk",
            inputs=[helper.make_tensor_value_info("crops", TensorProto.FLOAT, ["N", 1, 1, 32, 32])],
            outputs=[helper.make_tensor_value_info("logits", TensorProto.FLOAT, ["N", 1, 1])],
            initializer=list(g.initializer),
        )
        scan_model = helper.make_model(outer, opset_imports=list(model.opset_import), ir_version=model.ir_version)
        onnx.checker.check_model(scan_model)
        scan_bytes = scan_model.SerializeToString()
        # One session PER WORKER, all from the same bytes: concurrent Run() calls on a single
        # session serialize when the graph contains a Scan (see the header comment), and a
        # session is only ever borrowed by one task at a time, so this queue is what makes the
        # workers actually concurrent. Never more borrowers than sessions, so get() cannot block.
        self._scan_sessions: SimpleQueue = SimpleQueue()
        for _ in range(POOL_WORKERS):
            self._scan_sessions.put(ort.InferenceSession(scan_bytes, sess_options=opts, providers=["CPUExecutionProvider"]))
        self._scan_input = "crops"

        self._pool = ThreadPoolExecutor(max_workers=POOL_WORKERS, thread_name_prefix="patch-scorer")

    def _scan_logits(self, stacked_u8: np.ndarray) -> np.ndarray:
        """One chunk, one Run: the k uint8 crops in `stacked_u8` become float and go through the
        Scan-wrapped per-crop graph in a single GIL-released call, coming back as k logits in
        input order. The float conversion here is byte-identical to extract_crop's: uint8 to
        float32 is exact for every value 0..255, and IEEE division is elementwise, so casting
        and dividing the whole chunk at once produces the same bytes as doing each crop alone."""
        x = stacked_u8.astype(np.float32)
        x /= 255.0
        sess = self._scan_sessions.get()
        try:
            return sess.run(None, {self._scan_input: x})[0].ravel()
        finally:
            self._scan_sessions.put(sess)

    def score(self, page: Page, boxes: list[Box]) -> np.ndarray:
        """p(filled) per box. Each crop is still quantized and scored alone (one Scan iteration
        per crop, no batch axis, no statistics shared between crops), so every logit is
        bit-for-bit what the original one-crop-at-a-time loop produces. Extraction stays on the
        main thread (measured: moving it into the workers collides six GIL-holding extraction
        phases at drain start and loses ~0.3-0.5 ms) and is pipelined: each chunk is submitted
        the moment its crops are resized, so workers scan chunk i while i+1 is extracted."""
        n = len(boxes)
        if n == 0:
            return np.array([])
        gray = page.gray
        # All window geometry in one vectorized pass instead of ~2 property calls, 4 min/max and
        # 4 int() per crop. Same arithmetic as _crop_u8 to the bit: b.w is b.x2 - b.x1, the
        # products run in the same IEEE double precision, and astype(int64) truncates toward
        # zero exactly like int() for these non-negative widths. tolist() hands the slicing loop
        # plain Python ints, which index faster than numpy scalars.
        g = np.empty((4, n), np.int64)
        for j, b in enumerate(boxes):
            g[0, j], g[1, j], g[2, j], g[3, j] = b.x1, b.y1, b.x2, b.y2
        gx = ((g[2] - g[0]) * GROW).astype(np.int64)
        gy = ((g[3] - g[1]) * GROW).astype(np.int64)
        x1s = np.maximum(0, g[0] - gx).tolist()
        y1s = np.maximum(0, g[1] - gy).tolist()
        x2s = np.minimum(gray.shape[1], g[2] + gx).tolist()
        y2s = np.minimum(gray.shape[0], g[3] + gy).tolist()
        futures = []
        i = 0
        for size in _schedule(n):
            stacked = np.empty((size, 1, 1, CROP, CROP), np.uint8)
            for j in range(size):
                k = i + j
                dst = stacked[j, 0, 0]
                if x2s[k] > x1s[k] and y2s[k] > y1s[k]:
                    # resize straight into the chunk buffer: same INTER_AREA values as
                    # _crop_u8, minus one allocation and one copy per crop
                    cv2.resize(gray[y1s[k] : y2s[k], x1s[k] : x2s[k]], (CROP, CROP), dst=dst, interpolation=cv2.INTER_AREA)
                else:
                    dst[:] = 255  # the empty-window branch of _crop_u8
            i += size
            futures.append(self._pool.submit(self._scan_logits, stacked))
        logits = [lg for f in futures for lg in f.result()]
        # Sigmoid stays a plain per-element Python loop, matching the original scalar formula
        # exactly, so this can't introduce a vectorized-vs-scalar rounding difference on top.
        return np.array([1.0 / (1.0 + np.exp(-float(lg))) for lg in logits])


def load_scorer(path: Path = MODEL_PATH) -> PatchScorer | None:
    import os

    if os.environ.get("HV_CLASSIFIER", "").lower() in {"off", "0", "none"}:
        return None
    if not path.exists():
        return None
    try:
        return PatchScorer(path)
    except Exception:
        return None


def apply_model(page: Page, boxes: list[Box], scorer: PatchScorer) -> None:
    if not boxes:
        return
    probs = scorer.score(page, boxes)
    for b, p in zip(boxes, probs):
        model_says = p > 0.5
        if model_says == b.is_checked:
            b.confidence = round(max(b.confidence, min(0.98, 0.5 + abs(p - 0.5))), 4)
        else:
            b.reasons = b.reasons + ["CLASSIFIER_DISAGREE"]
            b.confidence = round(min(b.confidence, 0.4), 4)
