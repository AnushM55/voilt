from pathlib import Path

from scripts.train_edge_model import build_command


def test_training_command_builder() -> None:
    command = build_command(Path("dataset/data.yaml"), "yolo11n.pt", 60, 640)
    assert "yolo detect train" in command
    assert "data=dataset/data.yaml" in command
