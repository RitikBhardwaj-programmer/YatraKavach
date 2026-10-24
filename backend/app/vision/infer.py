"""DM-Count crowd counting on CPU with onnxruntime (pure: no DB). docs/PLAN.md "Camera crowd count".

The model maps an RGB image to a density map at 1/8 resolution; the crowd count is the sum of that map.
Preprocessing follows DM-Count (datasets/crowd.py): RGB in [0, 1], ImageNet mean/std, NCHW float32.
"""
import hashlib
import io
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

from app.risk.config import thresholds

VISION_DIR = Path(__file__).resolve().parent
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
# Jet colour map control points (value, R, G, B); same look as the DM-Count demo, without OpenCV/matplotlib.
_JET = np.array([[0.0, 0, 0, 128], [0.125, 0, 0, 255], [0.375, 0, 255, 255], [0.625, 255, 255, 0],
                 [0.875, 255, 0, 0], [1.0, 128, 0, 0]], dtype=np.float32)


class ModelChecksumError(RuntimeError):
    """The model file is missing, unpinned in config, or its sha256 differs from `vision.model_sha256`."""


class UnreadableImage(ValueError):
    """The uploaded bytes are not an image Pillow can decode."""


@dataclass(frozen=True)
class Result:
    count: float
    density: np.ndarray       # (H/8, W/8) persons per density-map cell
    heatmap_png: bytes
    ms: float                 # model inference time only (preprocessing and PNG encoding excluded)


def vision_config() -> dict:
    return thresholds()["vision"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_session(path: Path, expected_sha256: str | None):
    """An onnxruntime CPU session for `path`, after checking its sha256 against the pinned value."""
    import onnxruntime as ort

    if not expected_sha256:
        raise ModelChecksumError("vision.model_sha256 is not set in config/thresholds.yaml; run "
                                 "scripts/export_dmcount_onnx.py")
    if not path.exists():
        raise ModelChecksumError(f"model file {path} not found; run scripts/export_dmcount_onnx.py")
    actual = sha256_file(path)
    if actual != expected_sha256.lower():
        raise ModelChecksumError(f"sha256 of {path.name} is {actual}, config expects {expected_sha256}")
    return ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])


_session = None
_lock = threading.Lock()


def session():
    """The configured model, loaded once on first use."""
    global _session
    with _lock:
        if _session is None:
            cfg = vision_config()
            _session = load_session(VISION_DIR / cfg["model_file"], cfg["model_sha256"])
    return _session


def decode_image(data: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as e:
        raise UnreadableImage(f"not a readable image: {e}") from e
    return img.convert("RGB")


def resize_max_side(img: Image.Image, max_side: int) -> Image.Image:
    """Downscale so the longer side is at most `max_side` (never upscale)."""
    w, h = img.size
    scale = max_side / max(w, h)
    if scale >= 1.0:
        return img
    return img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.BICUBIC)


def to_tensor(img: Image.Image) -> np.ndarray:
    """RGB image -> normalised NCHW float32, as torchvision ToTensor + Normalize in DM-Count."""
    x = np.asarray(img, dtype=np.float32) / 255.0
    x = (x - MEAN) / STD
    return np.ascontiguousarray(x.transpose(2, 0, 1)[None])


def density_map(sess, x: np.ndarray) -> np.ndarray:
    """Run the model; returns the (h, w) density map as float32."""
    inp = sess.get_inputs()[0]
    if inp.type == "tensor(float16)":
        x = x.astype(np.float16)
    out = sess.run(None, {inp.name: x})[0]
    return np.asarray(out, dtype=np.float32).reshape(out.shape[-2], out.shape[-1])


def colourise(values: np.ndarray) -> np.ndarray:
    """Values in [0, 1] -> uint8 RGB with the jet colour map."""
    v = np.clip(values, 0.0, 1.0)
    rgb = [np.interp(v, _JET[:, 0], _JET[:, i]) for i in (1, 2, 3)]
    return np.stack(rgb, axis=-1).round().astype(np.uint8)


def heatmap_png(img: Image.Image, density: np.ndarray, alpha: float) -> bytes:
    """The density map (normalised to its maximum) in jet colours, blended over the image, as PNG bytes."""
    peak = float(density.max()) if density.size else 0.0
    norm = density / peak if peak > 0 else np.zeros_like(density)
    small = Image.fromarray((norm * 255).round().astype(np.uint8), mode="L")
    norm_full = np.asarray(small.resize(img.size, Image.BILINEAR), dtype=np.float32) / 255.0
    overlay = Image.fromarray(colourise(norm_full), mode="RGB")
    buf = io.BytesIO()
    Image.blend(img.convert("RGB"), overlay, alpha).save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def count_image(img: Image.Image, sess=None, max_side: int | None = None, alpha: float | None = None) -> Result:
    """Count people in `img`. Defaults come from `vision` in config/thresholds.yaml."""
    cfg = vision_config()
    sess = session() if sess is None else sess
    img = resize_max_side(img.convert("RGB"), int(max_side or cfg["max_side_px"]))
    x = to_tensor(img)
    t0 = time.perf_counter()
    density = density_map(sess, x)
    ms = (time.perf_counter() - t0) * 1000.0
    count = float(density.sum(dtype=np.float64))
    return Result(count, density, heatmap_png(img, density, float(alpha if alpha is not None else cfg["heatmap_alpha"])),
                  round(ms, 1))
