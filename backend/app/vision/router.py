"""Vision HTTP API (docs/PLAN.md "HTTP API contract"). Mounted at /api by app.main."""
import base64

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app import db
from app.vision import infer, service

router = APIRouter(tags=["vision"])


@router.get("/vision/cameras")
def vision_cameras() -> list[dict]:
    return service.cameras()


@router.get("/vision/samples")
def vision_samples() -> list[dict]:
    return service.samples()


@router.get("/vision/samples/{name}")
def vision_sample(name: str) -> FileResponse:
    path = service.sample_path(name)
    if path is None:
        raise HTTPException(404, f"sample {name} not found")
    return FileResponse(path)


def _model_label() -> str:
    cfg = infer.vision_config()
    return cfg.get("model_label") or f"DM-Count ({cfg['model_file']})"


@router.post("/vision/count")
def vision_count(camera_id: str, persist: bool = False, image: UploadFile | None = File(None),
                 sample: str | None = Form(None)) -> dict:
    """Count people in an uploaded photo or a demo sample; `persist=true` writes the live crowd row (not SIMULATED)."""
    cam = service.camera(camera_id)
    if cam is None:
        raise HTTPException(404, f"camera {camera_id} not found")
    if (image is None) == (sample is None):
        raise HTTPException(422, "send exactly one of: multipart field `image`, form field `sample`")
    if persist and sample is not None:
        raise HTTPException(422, "a demo photo is not a camera image and cannot be applied to the live crowd")
    if sample is not None:
        path = service.sample_path(sample)
        if path is None:
            raise HTTPException(404, f"sample {sample} not found")
        data = path.read_bytes()
    else:
        limit = int(infer.vision_config()["max_upload_bytes"])
        data = image.file.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(413, f"image is larger than {limit} bytes")
    try:
        img = infer.decode_image(data)
    except infer.UnreadableImage as e:
        raise HTTPException(422, str(e)) from e
    try:
        result = infer.count_image(img)
    except infer.ModelChecksumError as e:
        raise HTTPException(503, str(e)) from e
    with db.conn() as c:
        crowd = service.measure(c, cam, result.count)
        if persist:
            service.persist(c, cam, crowd, service.current_hour())
    return {"camera_id": cam["id"], "segment_id": cam["segment_id"], "count": round(result.count, 1), **crowd,
            "heatmap_png_b64": base64.b64encode(result.heatmap_png).decode("ascii"), "model": _model_label(),
            "demo_image": sample is not None, "ms": result.ms, "persisted": persist}
