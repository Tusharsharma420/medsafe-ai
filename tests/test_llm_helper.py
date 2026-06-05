from unittest.mock import MagicMock
from utils.llm_helper import summarize_interaction, get_symptom_guidance

def test_summarize_interaction(mocker):
    """Test summarize_interaction with a mocked Gemini model response."""
    # Mock the response object
    mock_response = MagicMock()
    mock_response.text = "This combination is dangerous because of bleeding risk."
    
    # Mock the generation_model instance inside utils.llm_helper
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    
    mocker.patch('utils.llm_helper.generation_model', mock_model)
    mocker.patch('utils.llm_helper.api_key', "fake_key")
    
    summary = summarize_interaction("Aspirin", "Warfarin", "High", "Increased risk of bleeding.")
    assert "dangerous" in summary
    mock_model.generate_content.assert_called_once()

def test_get_symptom_guidance(mocker):
    """Test get_symptom_guidance with a mocked Gemini model response."""
    mock_response = MagicMock()
    mock_response.text = "RISK_LEVEL: High\nGUIDANCE:\nPlease seek medical assistance."
    
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    
    mocker.patch('utils.llm_helper.generation_model', mock_model)
    mocker.patch('utils.llm_helper.api_key', "fake_key")
    
    guidance, risk_level = get_symptom_guidance(30, "Male", "Aspirin", "I feel extremely dizzy and short of breath")
    assert risk_level == "High"
    assert "medical assistance" in guidance
    mock_model.generate_content.assert_called_once()
