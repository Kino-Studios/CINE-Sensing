from pathlib import Path


def test_writer_emits_source_of_truth_banner():
    src = Path(__file__).resolve().parents[2] / "launch" / "generate_vins_config.py"
    text = src.read_text()
    # The writer must emit a banner that names the JSON source of truth so the
    # generated yaml cannot be silently hand-edited (which produces invalid metrics).
    assert "DO NOT EDIT" in text, "writer must emit a DO-NOT-EDIT banner"
    assert "configs/json/vins.json" in text, "banner must name the source of truth"
