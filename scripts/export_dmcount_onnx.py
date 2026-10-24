"""One-off: export DM-Count (ShanghaiTech A weights) to ONNX for backend/app/vision (docs/PLAN.md "Camera crowd count").

Needs torch, onnx and onnxconverter-common (NOT in backend/requirements.txt), plus:
  - the official code: git clone https://github.com/cvlab-stonybrook/DM-Count  (MIT)
  - the ShanghaiTech A weights `model_sha.pth` from the Google Drive folder linked in its README.

  python scripts/export_dmcount_onnx.py --dmcount-src DM-Count --weights model_sha.pth --check a.jpg b.jpg

Steps: build DM-Count's VGG19 head (no ImageNet download), load the weights, export with dynamic height/width
(opset 17), check onnxruntime vs torch counts on the --check images (< 1 % apart), convert to fp16 and keep it only
if its counts stay within 1 % of fp32, copy the chosen file to backend/app/vision/model/ (< 95 MB), and pin name, sha256 and a
label in the `vision:` block of config/thresholds.yaml.

Fallback (`--onnx`): pin an already exported DM-Count ONNX (e.g. the Luxonis export of DM-Count SHA, MIT) after the
same fp16 decision; torch is then not needed and the torch parity check is skipped (say so in the PR).
"""
import argparse
import hashlib
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.vision.infer import count_image, decode_image  # noqa: E402

MODEL_DIR = REPO / "backend/app/vision/model"
CONFIG = REPO / "config/thresholds.yaml"
OPSET = 17
MAX_REL_DIFF = 0.01      # brief: onnxruntime vs torch, and fp16 vs fp32, within 1 %
MAX_MB = 95.0            # brief: the shipped file must stay under 95 MB (GitHub's 100 MB limit)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def rel_diff(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1e-6)


def build_torch_model(dmcount_src: Path, weights: Path):
    """DM-Count's VGG with the given weights. Uses VGG(make_layers(cfg['E'])) so no ImageNet weights are fetched."""
    import torch

    sys.path.insert(0, str(dmcount_src))
    from models import VGG, cfg, make_layers  # DM-Count models.py

    model = VGG(make_layers(cfg["E"]))
    state = torch.load(weights, map_location="cpu", weights_only=True)
    model.load_state_dict(state)  # strict: every layer must come from the SHA weights
    model.eval()

    class DensityOnly(torch.nn.Module):
        def __init__(self, m):
            super().__init__()
            self.m = m

        def forward(self, x):
            return self.m(x)[0]  # the density map; the normalised map is training-only

    return DensityOnly(model).eval()


def export_onnx(model, out: Path) -> None:
    import torch

    dummy = torch.zeros(1, 3, 512, 768)
    torch.onnx.export(model, dummy, str(out), opset_version=OPSET, input_names=["image"], output_names=["density"],
                      dynamic_axes={"image": {2: "height", 3: "width"}, "density": {2: "dh", 3: "dw"}},
                      do_constant_folding=True, dynamo=False)


def session(path: Path):
    import onnxruntime as ort
    return ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])


def ort_counts(path: Path, images: list) -> list[float]:
    s = session(path)
    return [count_image(img, s).count for img in images]


def torch_counts(model, images: list) -> list[float]:
    import torch

    from app.vision.infer import resize_max_side, to_tensor, vision_config
    out = []
    with torch.no_grad():
        for img in images:
            x = torch.from_numpy(to_tensor(resize_max_side(img, int(vision_config()["max_side_px"]))))
            out.append(float(model(x).sum()))
    return out


def to_fp16(src: Path, dst: Path) -> None:
    import onnx
    from onnxconverter_common import float16

    m = float16.convert_float_to_float16(onnx.load(str(src)), keep_io_types=True)
    onnx.save(m, str(dst))


def pin_config(model_file: str, digest: str, label: str, path: Path = CONFIG) -> None:
    """Rewrite the three pinned values in the `vision:` block, keeping the comments."""
    text = path.read_text(encoding="utf-8")
    block = text.index("\nvision:")
    head, tail = text[:block], text[block:]
    for key, value in (("model_file", model_file), ("model_sha256", digest), ("model_label", f'"{label}"')):
        tail, n = re.subn(rf"(\n  {key}: )\S.*?(\s+#|\n)", lambda m: f"{m.group(1)}{value}{'  #' if m.group(2).strip() else m.group(2)}", tail, count=1)
        if n != 1:
            raise SystemExit(f"vision.{key} not found in {path}")
    path.write_text(head + tail, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dmcount-src", type=Path, help="clone of cvlab-stonybrook/DM-Count")
    ap.add_argument("--weights", type=Path, help="DM-Count ShanghaiTech A weights (model_sha.pth)")
    ap.add_argument("--onnx", type=Path, help="fallback: an existing DM-Count SHA ONNX file (e.g. Luxonis)")
    ap.add_argument("--source", default="official weights", help="where the weights came from, for the label")
    ap.add_argument("--check", type=Path, nargs=2, required=True, help="two crowd photos for the parity checks")
    ap.add_argument("--work-dir", type=Path, required=True,
                    help="outside the repo: keeps both fp32 and fp16 files (eval_vision.py --fp32 uses the fp32 one)")
    ap.add_argument("--name", default="dmcount_sha")
    a = ap.parse_args()
    images = [decode_image(p.read_bytes()) for p in a.check]
    a.work_dir.mkdir(parents=True, exist_ok=True)
    fp32, fp16 = a.work_dir / f"{a.name}_fp32.onnx", a.work_dir / f"{a.name}_fp16.onnx"

    if a.onnx:
        shutil.copyfile(a.onnx, fp32)
        print(f"using given ONNX {a.onnx} (torch parity check skipped)")
    else:
        if not (a.dmcount_src and a.weights):
            raise SystemExit("give --dmcount-src and --weights, or --onnx")
        model = build_torch_model(a.dmcount_src, a.weights)
        export_onnx(model, fp32)
        t, o = torch_counts(model, images), ort_counts(fp32, images)
        for p, ct, co in zip(a.check, t, o):
            print(f"{p.name}: torch {ct:.2f}  onnxruntime fp32 {co:.2f}  diff {rel_diff(co, ct):.4%}")
            if rel_diff(co, ct) >= MAX_REL_DIFF:
                raise SystemExit("onnxruntime count differs from torch by >= 1 %")

    to_fp16(fp32, fp16)
    c32, c16 = ort_counts(fp32, images), ort_counts(fp16, images)
    worst = max(rel_diff(b, x) for b, x in zip(c16, c32))
    for p, x, b in zip(a.check, c32, c16):
        print(f"{p.name}: fp32 {x:.2f}  fp16 {b:.2f}  diff {rel_diff(b, x):.4%}")
    src, precision = (fp16, "fp16") if worst < MAX_REL_DIFF else (fp32, "fp32")
    mb = src.stat().st_size / 1e6
    if mb >= MAX_MB:
        raise SystemExit(f"{src.name} is {mb:.1f} MB (limit {MAX_MB} MB)")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    shipped = MODEL_DIR / src.name
    shutil.copyfile(src, shipped)
    digest = sha256(shipped)
    pin_config(f"model/{shipped.name}", digest, f"DM-Count ShanghaiTech A ({a.source}), {precision}")
    print(f"kept {precision} (worst fp16 vs fp32 diff {worst:.4%}); {shipped.relative_to(REPO)} {mb:.1f} MB "
          f"sha256 {digest}; pinned in {CONFIG.relative_to(REPO)}")
    print(f"fp32 sha256 {sha256(fp32)} ({fp32})")


if __name__ == "__main__":
    main()
