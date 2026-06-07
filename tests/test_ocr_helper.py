"""Tests for ocr_helper.py — error handling and JSON parsing logic."""
import pytest
import json
from unittest.mock import patch, MagicMock
import utils.ocr_helper as ocr_mod


class TestExtractPrescriptionData:
    """Tests for the OCR extraction pipeline."""

    def test_no_api_key_returns_error_dict(self):
        with patch.object(ocr_mod, "api_key", None):
            result = ocr_mod.extract_prescription_data("fake_path.jpg")
            assert isinstance(result, dict)
            assert "error" in result
            assert "API Key not configured" in result["error"]

    def test_valid_json_response_is_parsed(self, tmp_path):
        """A well-formed LLM response should return a parsed list."""
        fake_image = tmp_path / "test.jpg"
        fake_image.write_bytes(b"\xff\xd8\xff")  # minimal JPEG header bytes

        mock_response = MagicMock()
        mock_response.text = json.dumps([
            {"name": "Aspirin 100mg", "active_salt": "Acetylsalicylic acid"},
            {"name": "Paracetamol", "active_salt": "Acetaminophen"},
        ])
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        mock_img = MagicMock()
        mock_pil = MagicMock()
        mock_pil.__enter__ = lambda s: mock_img
        mock_pil.__exit__ = MagicMock(return_value=False)

        with patch.object(ocr_mod, "api_key", "fake-key"):
            with patch.object(ocr_mod, "vision_model", mock_model):
                with patch("PIL.Image.open", return_value=mock_pil):
                    result = ocr_mod.extract_prescription_data(str(fake_image))
                    assert isinstance(result, list), f"Expected list, got: {result}"
                    assert len(result) == 2
                    assert result[0]["name"] == "Aspirin 100mg"

    def test_markdown_fenced_json_is_handled(self, tmp_path):
        """LLM sometimes returns ```json ... ``` — this should be stripped."""
        fake_image = tmp_path / "test.png"
        fake_image.write_bytes(b"fake")

        medicines = [{"name": "Warfarin 5mg", "active_salt": "Warfarin sodium"}]
        mock_response = MagicMock()
        mock_response.text = f"```json\n{json.dumps(medicines)}\n```"
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        mock_img = MagicMock()
        mock_pil = MagicMock()
        mock_pil.__enter__ = lambda s: mock_img
        mock_pil.__exit__ = MagicMock(return_value=False)

        with patch.object(ocr_mod, "api_key", "fake-key"):
            with patch.object(ocr_mod, "vision_model", mock_model):
                with patch("PIL.Image.open", return_value=mock_pil):
                    result = ocr_mod.extract_prescription_data(str(fake_image))
                    assert isinstance(result, list), f"Expected list, got: {result}"
                    assert result[0]["active_salt"] == "Warfarin sodium"

    def test_invalid_json_response_returns_error(self, tmp_path):
        """If LLM returns non-JSON, return an error dict."""
        fake_image = tmp_path / "test.jpg"
        fake_image.write_bytes(b"fake")

        mock_response = MagicMock()
        mock_response.text = "I cannot read this prescription clearly."
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        mock_img = MagicMock()
        mock_pil = MagicMock()
        mock_pil.__enter__ = lambda s: mock_img
        mock_pil.__exit__ = MagicMock(return_value=False)

        with patch.object(ocr_mod, "api_key", "fake-key"):
            with patch.object(ocr_mod, "vision_model", mock_model):
                with patch("PIL.Image.open", return_value=mock_pil):
                    result = ocr_mod.extract_prescription_data(str(fake_image))
                    assert isinstance(result, dict)
                    assert "error" in result

    def test_api_exception_returns_error_dict(self, tmp_path):
        """Network/API exceptions should result in an error dict, never a crash."""
        fake_image = tmp_path / "test.jpg"
        fake_image.write_bytes(b"fake")

        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("Connection timeout")

        mock_img = MagicMock()
        mock_pil = MagicMock()
        mock_pil.__enter__ = lambda s: mock_img
        mock_pil.__exit__ = MagicMock(return_value=False)

        with patch.object(ocr_mod, "api_key", "fake-key"):
            with patch.object(ocr_mod, "vision_model", mock_model):
                with patch("PIL.Image.open", return_value=mock_pil):
                    result = ocr_mod.extract_prescription_data(str(fake_image))
                    assert isinstance(result, dict)
                    assert "error" in result
                    assert "Connection timeout" in result["error"] or "Error" in result["error"]
