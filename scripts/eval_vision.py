"""MAE of the shipped DM-Count ONNX model on the ShanghaiTech Part A test set (182 images).

Needs scipy (for the ground-truth .mat files; not in backend/requirements.txt) and the dataset laid out as
released: <data>/images/IMG_<n>.jpg and <data>/ground_truth/GT_IMG_<n>.mat (part_A_final/test_data; some mirrors
name the folder ground-truth, which also works).

  python scripts/eval_vision.py --data ShanghaiTech/part_A_final/test_data [--fp32 work/dmcount_sha_fp32.onnx]

Runs the same path as the API (app.vision.infer.count_image: resize to max_side_px, ImageNet normalisation,
count = sum of the density map). The ground-truth count is the number of annotated heads. DM-Count's own test.py
uses the full image; SHA test images are at most 1024 px, below max_side_px, so the input is the same.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.vision import infer  # noqa: E402


def gt_count(mat_path: Path) -> int:
    from scipy.io import loadmat
    return int(loadmat(str(mat_path))["image_info"][0][0][0][0][0].shape[0])


def gt_dir(data: Path) -> Path:
    for name in ("ground_truth", "ground-truth"):
        if (data / name).is_dir():
            return data / name
    raise SystemExit(f"no ground_truth folder in {data}")


def evaluate(sess, data: Path) -> dict:
    images = sorted((data / "images").glob("*.jpg"))
    if not images:
        raise SystemExit(f"no images in {data / 'images'}")
    gts_dir = gt_dir(data)
    errs, gts, ms = [], [], []
    for p in images:
        gt = gt_count(gts_dir / f"GT_{p.stem}.mat")
        r = infer.count_image(infer.decode_image(p.read_bytes()), sess)
        errs.append(r.count - gt)
        gts.append(gt)
        ms.append(r.ms)
    e = np.array(errs)
    return {"images": len(images), "mae": round(float(np.mean(np.abs(e))), 2),
            "rmse": round(float(np.sqrt(np.mean(e ** 2))), 2), "mean_gt": round(float(np.mean(gts)), 1),
            "mean_ms": round(float(np.mean(ms)), 1)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, required=True, help="ShanghaiTech part_A_final/test_data")
    ap.add_argument("--fp32", type=Path, help="also evaluate this unshipped fp32 export (from --work-dir)")
    a = ap.parse_args()
    cfg = infer.vision_config()
    out = {"shipped": {"model": cfg["model_file"], **evaluate(infer.session(), a.data)}}
    if a.fp32:
        sess = infer.load_session(a.fp32, infer.sha256_file(a.fp32))
        out["fp32"] = {"model": a.fp32.name, **evaluate(sess, a.data)}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
