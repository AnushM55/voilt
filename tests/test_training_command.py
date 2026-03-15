import sys

from scripts.train import parse_args


def test_training_parse_args_defaults(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["train.py"])

    args = parse_args()

    assert args.data == "dataset/data.yaml"
    assert args.model == "yolo11n.pt"
    assert args.epochs == 100
    assert args.imgsz == 640
    assert args.batch == 16
    assert args.device == "0"
    assert args.project == "runs"
    assert args.name == "voilt-edge"
