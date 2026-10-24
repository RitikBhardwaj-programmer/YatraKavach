# Brief: workstream V — camera crowd count (computer vision)

Read `CLAUDE.md` and `docs/PLAN.md` first; they are binding (see "Camera crowd count" and the vision endpoints in
"HTTP API"). Work on branch `ws-v-vision` and open a PR to `main`. Two other sessions work at the same time
(I: impact, U: console). Touch only V's paths: `backend/app/vision/`, `backend/tests/vision/`,
`scripts/export_dmcount_onnx.py`, `scripts/eval_vision.py`, `backend/requirements.txt`, and the `vision:` block of
`config/thresholds.yaml`.

## Build
1. `scripts/export_dmcount_onnx.py` (a one-off script; torch is NOT added to `backend/requirements.txt`):
   - Get the official DM-Count code and the ShanghaiTech **A** pretrained weights
     (https://github.com/cvlab-stonybrook/DM-Count, MIT; weights linked from its README, Google Drive; `gdown` may work).
   - Export to ONNX with dynamic height/width, opset >= 17. Check that onnxruntime output matches torch on 2 images
     (relative count difference < 1%). Convert to fp16 (`onnxconverter-common`) if the fp16 count stays within 1% of
     fp32; else keep fp32. Save as `backend/app/vision/model/<name>.onnx` (it must stay under 95 MB).
   - Write the file's sha256 and name into `vision.model_sha256` / `vision.model_file` in `config/thresholds.yaml`.
   - If the official weights cannot be downloaded, try the Luxonis ONNX export of DM-Count SHA
     (https://models.luxonis.com/luxonis/dm-count, MIT) and say which one you used. If neither works, say exactly
     what failed and stop.
2. `backend/app/vision/` with `__init__.py`, `infer.py`, `service.py`, `router.py` (exposes `router`; `main.py`
   already loads `app.vision.router`):
   - `infer.py` is pure (no DB): load the model once (lazy), check its sha256 against config, resize so the longer
     side is `vision.max_side_px`, normalise as DM-Count does (ImageNet mean/std, RGB), run, return
     `count = sum(density map)`, the density map, and a heatmap PNG (numpy colour map blended over the image,
     Pillow; no matplotlib, no OpenCV).
   - `service.py`: cameras from `vision.cameras`; density = count / view_area_m2; persons_on_segment =
     density x segment length_m x width_m (from the `segments` table); level with `crowd.bands_ppm2` (reuse
     `app.crowd.simulator.density_level`). `persist=true`: upsert the live `segment_crowd` row for the camera's
     segment at the current IST hour with `simulated=false` and `scenario={"source":"camera","camera_id":...}`
     (reuse the upsert in `app.crowd.service`), then call `app.risk.service.run_risk(c, "live", hour, hour)`.
   - `router.py`: the four vision endpoints exactly as in `docs/PLAN.md`, with the status codes listed there.
     Add `"ms"` (inference time in milliseconds).
3. Demo photos: 3-5 photos of dense crowds (Indian pilgrimages or festivals preferred) from Wikimedia Commons with
   a CC0, CC BY or CC BY-SA licence. Check each licence on the file page. Resize to at most 1280 px, save in
   `backend/app/vision/samples/`, and list each in `backend/app/vision/samples/ATTRIBUTION.md`
   (file, title, author, licence, source URL). `GET /api/vision/samples` reads that list. If you cannot confirm a
   licence, leave the photo out. If no photo qualifies, say so and stop.
4. `backend/requirements.txt`: add pinned `onnxruntime`, `numpy`, `pillow`, `python-multipart` (versions with
   Python 3.12 wheels). Nothing else.
5. `scripts/eval_vision.py`: mean absolute error (MAE) and the mean ground-truth count on the ShanghaiTech Part A test
   set, for the shipped ONNX model (and fp32 if you converted to fp16). If the dataset cannot be downloaded, say
   so; do not invent numbers.
6. Tests in `backend/tests/vision/` (no DB needed): inference on a synthetic image (shape, count >= 0,
   same result twice); density, persons and level maths; sha256 mismatch raises; router returns 404 for an
   unknown camera or sample (use FastAPI's TestClient; skip DB-backed cases with a clear message when no DB).

## Check your work
- `cd backend && pytest tests/vision` passes. If Docker or PostGIS is available, also run the full `pytest`.
- Run the count on every sample and put a table in the PR: file, count, ms on CPU.
- Put the MAE result (or the exact reason it is missing) in the PR.

## Done
PR open with: what was exported and from where, the model size and sha256, the sample table, the MAE, and what
you could not check. Commit messages are imperative and end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; the PR body ends with
`🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
If something you need is missing (a file, a secret, access, a tool, network), say exactly what and stop.
Never mock, substitute or guess real-world data.
