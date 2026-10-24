import io

import numpy as np
import pytest
from PIL import Image

from app.vision import infer


def synthetic(w: int = 320, h: int = 240) -> Image.Image:
    """A deterministic synthetic test pattern (not a photo): gradient plus blobs."""
    y, x = np.mgrid[0:h, 0:w]
    rgb = np.stack([(x * 255 // w), (y * 255 // h), ((x + y) % 64) * 4], axis=-1).astype(np.uint8)
    for cx, cy in ((60, 60), (160, 120), (250, 180)):
        rgb[(x - cx) ** 2 + (y - cy) ** 2 < 100] = (30, 20, 10)
    return Image.fromarray(rgb, mode="RGB")


@pytest.mark.parametrize("size, max_side, expected", [
    ((2560, 1440), 1280, (1280, 720)), ((1000, 3000), 1280, (427, 1280)), ((640, 480), 1280, (640, 480))])
def test_resize_max_side(size, max_side, expected):
    assert infer.resize_max_side(Image.new("RGB", size), max_side).size == expected


def test_max_side_from_config():
    assert infer.vision_config()["max_side_px"] == 1280


def test_to_tensor_normalises_like_dmcount():
    x = infer.to_tensor(Image.new("RGB", (4, 2), (255, 0, 124)))
    assert x.shape == (1, 3, 2, 4) and x.dtype == np.float32
    expected = (np.array([1.0, 0.0, 124 / 255]) - infer.MEAN) / infer.STD
    np.testing.assert_allclose(x[0, :, 0, 0], expected, rtol=1e-6)


def test_colourise_jet_ends():
    rgb = infer.colourise(np.array([0.0, 0.5, 1.0]))
    assert rgb[0].tolist() == [0, 0, 128] and rgb[2].tolist() == [128, 0, 0]
    assert rgb[1][1] == 255  # middle of jet is green/yellow-ish


def test_heatmap_png_matches_image_size():
    img = synthetic()
    density = np.zeros((30, 40), dtype=np.float32)
    density[10, 20] = 3.0
    png = infer.heatmap_png(img, density, 0.5)
    out = Image.open(io.BytesIO(png))
    assert out.format == "PNG" and out.size == img.size


def test_heatmap_png_all_zero_density():
    assert infer.heatmap_png(synthetic(), np.zeros((30, 40), dtype=np.float32), 0.5).startswith(b"\x89PNG")


def test_decode_image_rejects_garbage():
    with pytest.raises(infer.UnreadableImage):
        infer.decode_image(b"not an image")


def _png(w: int, h: int) -> bytes:
    buf = io.BytesIO()
    synthetic(w, h).save(buf, format="PNG")
    return buf.getvalue()


def test_decode_image_size_limits():
    assert infer.decode_image(_png(320, 240)).size == (320, 240)
    with pytest.raises(infer.UnreadableImage, match="limit"):
        infer.decode_image(_png(320, 240), max_pixels=320 * 240 - 1)
    with pytest.raises(infer.UnreadableImage, match="shorter side"):
        infer.decode_image(_png(320, 20))


def test_decode_image_limits_from_config():
    cfg = infer.vision_config()
    assert cfg["max_image_pixels"] > 1280 * 1280 and cfg["min_side_px"] >= 8 and cfg["max_upload_bytes"] > 0


def test_sha256_mismatch_raises(tmp_path):
    f = tmp_path / "m.onnx"
    f.write_bytes(b"fake model bytes")
    with pytest.raises(infer.ModelChecksumError, match="sha256"):
        infer.load_session(f, "0" * 64)


def test_unpinned_sha256_raises(tmp_path):
    f = tmp_path / "m.onnx"
    f.write_bytes(b"x")
    with pytest.raises(infer.ModelChecksumError, match="not set"):
        infer.load_session(f, None)


def test_missing_model_raises(tmp_path):
    with pytest.raises(infer.ModelChecksumError, match="not found"):
        infer.load_session(tmp_path / "missing.onnx", "a" * 64)


def test_sha256_file(tmp_path):
    f = tmp_path / "x"
    f.write_bytes(b"abc")
    assert infer.sha256_file(f) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


# --- with the shipped model (skipped until it is exported and pinned) ---

def test_inference_on_synthetic_image(model):
    r = infer.count_image(synthetic(320, 240), model)
    assert r.density.shape == (30, 40)
    assert r.count >= 0.0 and np.isfinite(r.count)
    assert r.ms > 0 and r.heatmap_png.startswith(b"\x89PNG")


def test_inference_is_deterministic(model):
    a, b = infer.count_image(synthetic(), model), infer.count_image(synthetic(), model)
    assert a.count == b.count
    np.testing.assert_array_equal(a.density, b.density)


def test_large_image_is_downscaled_before_inference(model):
    r = infer.count_image(synthetic(2560, 1280), model)
    assert r.density.shape == (80, 160)  # 1280 x 640 input -> 1/8 resolution
