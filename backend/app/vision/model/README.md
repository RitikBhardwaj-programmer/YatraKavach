# Model

`scripts/export_dmcount_onnx.py` writes the ONNX file here and pins its name and sha256 in
`config/thresholds.yaml` (`vision.model_file`, `vision.model_sha256`). `app.vision.infer` refuses to load a file
whose sha256 differs. DM-Count: Wang et al., NeurIPS 2020, https://github.com/cvlab-stonybrook/DM-Count (MIT).
