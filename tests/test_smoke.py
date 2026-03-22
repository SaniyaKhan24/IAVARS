from agent.reasoning_engine import analyse_instruction
from data_processing.spreadsheet_reader import read_spreadsheet
from tools.url_validator import is_valid_url


def test_read_spreadsheet_sample_file() -> None:
    df = read_spreadsheet("data/input/sample_assets.xlsx")

    assert {"Brand", "Campaign", "Video Link"}.issubset(df.columns)
    assert len(df) > 0


def test_analyse_instruction_uses_local_fallback_when_no_api_key(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "")

    intent = analyse_instruction("Download only Nike videos and group by brand")

    assert intent["filter"] == "nike"
    assert intent["group_by"] == "brand"


def test_url_validator_accepts_http_and_https_only() -> None:
    assert is_valid_url("https://example.com/video")
    assert is_valid_url("http://example.com/video")
    assert not is_valid_url("ftp://example.com/video")
    assert not is_valid_url("")
