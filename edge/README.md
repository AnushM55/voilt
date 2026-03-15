# Edge Phase

Status: completed (`IMPLEMENTATION.md` Phase 1 marked complete).

## Scope
- Realtime violation detection pipeline on edge.
- Violations: `no_helmet` (direct), `triple_riding` (derived rule).
- No OCR on edge; backend-only OCR.
- Duplicate suppression via track-state + cooldown.
- Durable upload queue via SQLite.

## Dataflow
- `frame -> detector -> association -> tracker -> rules -> event -> sqlite queue -> uploader`
- On violation emit, edge stores `annotated_frame` and `motorcycle_crop` JPEG evidence.
- Uploader sends `multipart/form-data`: `event_json` + `evidence_*` files.

## Implemented Modules
- `edge/detector.py`: detector interface + stub adapter.
- `edge/association.py`: bike/person grouping by center-in-box.
- `edge/tracker_engine.py`: IoU-based motorcycle track assignment.
- `edge/rules.py`: temporal gating + violation decision + dedup filter.
- `edge/events.py`: shared payload construction + idempotency key.
- `edge/queue.py`: persistent queue (`enqueue`, `lease`, `ack`, retry-ready).
- `edge/uploader.py`: batched HTTP ingest with idempotency header.
- `edge/location.py`: coarse location provider with cache fallback.
- `edge/pipeline.py`: orchestration of detect/track/rule/emit/queue.
- `edge/main.py`: minimal edge worker entrypoint (`--once`).

## Contract
- Payload model: `shared/schemas.py::ViolationEvent`.
- Required fields include:
  - `event_id`, `idempotency_key`, `device_id`, `track_id`
  - `violations[]`, `max_confidence`, `motorcycle_bbox`, `counts`
  - `location{lat,lon,accuracy_m,source,timestamp}`
  - `model_version`, `software_version`, `evidence[]`

## Evidence transfer
- Edge evidence dir default: `edge/evidence/`.
- Server stores uploaded files under `server/uploads/<event_id>/`.
- Backend verifier can use stored paths from `payload.evidence` to re-run vision checks.
- Evidence image sent to backend is annotated (boxes + labels + track + violation text), not raw frame.

## Rule Semantics
- `no_helmet`: associated `no_helmet` person on motorcycle track.
- `triple_riding`: `rider + pillion >= 3` for same motorcycle track.
- Emit only after `min_stable_frames`.
- Dedup key behavior: once per `track_id + violation_type` within cooldown window.

## Runtime
- Config: `edge/config.py::EdgeSettings`.
- Smoke run (no detections expected): `uv run python -m edge.main --once`.
- Demo run (inject synthetic violating detections): `uv run python -m edge.main --once --demo-event`.
- Realtime camera loop (with model): `uv run python -m edge.main --realtime --source 0 --model <path-to-best.pt-or-ncnn-dir>`.
- Realtime headless mode: `uv run python -m edge.main --realtime --headless --source 0 --model <model>`.
- Realtime video file test: `uv run python -m edge.main --realtime --source /path/video.mp4 --model <model>`.
- Queue DB default: `edge/edge_queue.db`.

## How To Run
- Install deps: `uv sync`.
- Train model (GPU): `uv run python train.py --data dataset/data.yaml --model yolo11n.pt --epochs 60 --imgsz 640 --batch 16 --device 0 --project runs --name voilt-edge`.
- Trained weight path: `runs/detect/runs/voilt-edge/weights/best.pt`.
- NCNN export path: `runs/detect/runs/voilt-edge/weights/best_ncnn_model`.
- Start backend ingest (optional, for upload): `uv run uvicorn server.app:app --host 0.0.0.0 --port 8000`.
- Start realtime edge with camera: `uv run python -m edge.main --realtime --source 0 --model runs/detect/runs/voilt-edge/weights/best.pt --conf 0.15`.
- Start realtime edge headless: `uv run python -m edge.main --realtime --headless --source 0 --model runs/detect/runs/voilt-edge/weights/best.pt --conf 0.15`.
- Test with video file: `uv run python -m edge.main --realtime --source /absolute/path/test.mp4 --model runs/detect/runs/voilt-edge/weights/best.pt --conf 0.15`.
- Local-only mode (no backend POST): append `--no-upload`.
- Quit visual mode: press `q`.

## Verify It Works
- Visual mode: boxes/labels drawn over frames.
- Console stats every ~30 frames: `frames`, `fps`, `emitted`, `queue`, `uploaded`, `failed`.
- Local queue DB: `edge/edge_queue.db`.
- Evidence output: `edge/evidence/<track_id>/<timestamp>/`.
- Backend uploads (if enabled): `server/uploads/<event_id>/`.

## Why nothing spawned
- `--once` is intentionally single-shot; no loop, no camera, no uploader daemon.
- Current command validates pipeline wiring and queue persistence only.
- Without `--demo-event`, stub detector returns empty detections, so `enqueued=0` is expected.

## Realtime flags
- `--realtime`: starts continuous capture/infer/queue loop.
- `--source`: camera index (`0`) or video file path.
- `--model`: YOLO `.pt` or exported NCNN directory.
- `--headless`: disable OpenCV window.
- `--no-upload`: keep local queue only, skip backend POSTs.

## UI visibility note
- Display overlay now draws detector boxes/labels directly on frames in non-headless mode.
- If you only see raw video: check that `--model` points to your trained `best.pt`/`best_ncnn_model`.
- If still no boxes, lower threshold: `--conf 0.15`.

## Test Coverage
- `tests/test_edge_rules.py`: rule firing + dedup cooldown.
- `tests/test_edge_queue.py`: enqueue/lease/ack persistence semantics.
- `tests/test_edge_pipeline.py`: stable track emits once; repeat suppressed.
