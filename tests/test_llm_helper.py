"""Tests for llm_helper.py — focused on graceful degradation and output parsing."""
import pytest
from unittest.mock import patch, MagicMock
import utils.llm_helper as llm_mod


def make_mock_model(response_text):
    """Helper: create a mock GenerativeModel that returns response_text."""
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    return mock_model


class TestSummarizeInteractionDegradation:
    """Test graceful degradation when API key is absent."""

    def test_no_api_key_returns_error_string(self):
        # Simulate missing API key by patching module-level api_key
        with patch.object(llm_mod, "api_key", None):
            result = llm_mod.summarize_interaction("Aspirin", "Warfarin", "High", "Bleeding risk.")
            assert isinstance(result, str)
            assert "API Key not configured" in result

    def test_api_exception_returns_error_string(self):
        """If Gemini API throws, we should get an error string, not a crash."""
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("Network timeout")
        with patch.object(llm_mod, "api_key", "fake-key-for-testing"):
            with patch.object(llm_mod, "generation_model", mock_model):
                result = llm_mod.summarize_interaction("Aspirin", "Warfarin", "High", "Bleeding risk.")
                assert isinstance(result, str)
                assert "Error" in result

    def test_returns_string_type_always(self):
        """summarize_interaction must always return a string."""
        mock_model = make_mock_model("Aspirin and Warfarin interact. Consult your doctor.")
        with patch.object(llm_mod, "api_key", "fake-key-for-testing"):
            with patch.object(llm_mod, "generation_model", mock_model):
                result = llm_mod.summarize_interaction("Aspirin", "Warfarin", "High", "Bleeding risk.")
                assert isinstance(result, str)
                assert len(result) > 0


class TestGetSymptomGuidanceParsing:
    """Test risk level extraction from structured LLM output."""

    def test_parses_high_risk_correctly(self):
        text = "RISK_LEVEL: High\nGUIDANCE:\nYour symptoms indicate a serious issue. Please seek immediate care."
        mock_model = make_mock_model(text)
        with patch.object(llm_mod, "api_key", "fake-key-for-testing"):
            with patch.object(llm_mod, "generation_model", mock_model):
                guidance, risk_level = llm_mod.get_symptom_guidance(45, "Female", "Warfarin", "chest pain")
                assert risk_level == "High"
                assert "serious" in guidance.lower() or "care" in guidance.lower()

    def test_parses_low_risk_correctly(self):
        text = "RISK_LEVEL: Low\nGUIDANCE:\nYour symptoms seem mild. Rest and stay hydrated. Consult a doctor if they worsen."
        mock_model = make_mock_model(text)
        with patch.object(llm_mod, "api_key", "fake-key-for-testing"):
            with patch.object(llm_mod, "generation_model", mock_model):
                guidance, risk_level = llm_mod.get_symptom_guidance(25, "Male", "Paracetamol", "mild headache")
                assert risk_level == "Low"

    def test_parses_medium_risk_correctly(self):
        text = "RISK_LEVEL: Medium\nGUIDANCE:\nYour symptoms may need attention. Monitor closely and see a doctor soon."
        mock_model = make_mock_model(text)
        with patch.object(llm_mod, "api_key", "fake-key-for-testing"):
            with patch.object(llm_mod, "generation_model", mock_model):
                guidance, risk_level = llm_mod.get_symptom_guidance(40, "Female", "Metformin", "nausea")
                assert risk_level == "Medium"

    def test_malformed_response_falls_back_to_unknown(self):
        text = "I'm not sure what to say about your symptoms."  # No RISK_LEVEL marker
        mock_model = make_mock_model(text)
        with patch.object(llm_mod, "api_key", "fake-key-for-testing"):
            with patch.object(llm_mod, "generation_model", mock_model):
                guidance, risk_level = llm_mod.get_symptom_guidance(30, "Male", "", "headache")
                assert risk_level == "Unknown"
                assert isinstance(guidance, str)

    def test_no_api_key_returns_tuple(self):
        with patch.object(llm_mod, "api_key", None):
            guidance, risk_level = llm_mod.get_symptom_guidance(30, "Male", "", "headache")
            assert isinstance(guidance, str)
            assert isinstance(risk_level, str)
            assert "API Key not configured" in guidance

    def test_api_exception_returns_unknown(self):
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API error")
        with patch.object(llm_mod, "api_key", "fake-key-for-testing"):
            with patch.object(llm_mod, "generation_model", mock_model):
                guidance, risk_level = llm_mod.get_symptom_guidance(30, "Male", "", "headache")
                assert risk_level == "Unknown"
                assert isinstance(guidance, str)
