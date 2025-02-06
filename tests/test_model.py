import pytest

from beano.model import BedrockModel


class TestModel:
    def test_get_by_model_id_case_sensitivity(self):
        """
        Test get_by_model_id for case sensitivity.
        """
        result = BedrockModel.get_by_model_id(
            "ANTHROPIC.CLAUDE-3-5-HAIKU-20241022-V1:0"
        )
        assert result is None

    def test_get_by_model_id_empty_input(self):
        """
        Test get_by_model_id with an empty string input.
        """
        result = BedrockModel.get_by_model_id("")
        assert result is None

    def test_get_by_model_id_handles_empty_string(self):
        """
        Test that get_by_model_id handles an empty string input
        """
        result = BedrockModel.get_by_model_id("")
        assert result is None

    def test_get_by_model_id_invalid_input(self):
        """
        Test get_by_model_id with an invalid model_id.
        """
        result = BedrockModel.get_by_model_id("invalid_model_id")
        assert result is None

    def test_get_by_model_id_partial_match(self):
        """
        Test get_by_model_id with a partial match of an existing model_id.
        """
        result = BedrockModel.get_by_model_id("anthropic.claude-3-5-haiku")
        assert result is None

    def test_get_by_model_id_returns_correct_model(self):
        """
        Test that get_by_model_id returns the correct BedrockModel for a valid model_id
        """
        model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"
        result = BedrockModel.get_by_model_id(model_id)
        assert result == BedrockModel.ANTHROPIC_HAIKU_3_5
        assert result.value == "Claude 3.5 Haiku"
        assert result.model_id == model_id
        assert result.inference_profile == "us.anthropic.claude-3-5-haiku-20241022-v1:0"

    def test_get_by_model_id_returns_none_for_invalid_id(self):
        """
        Test that get_by_model_id returns None for an invalid model_id
        """
        invalid_model_id = "invalid.model.id"
        result = BedrockModel.get_by_model_id(invalid_model_id)
        assert result is None

    def test_get_by_value_case_sensitive(self):
        """
        Test that get_by_value is case-sensitive and raises a ValueError for incorrect casing.
        """
        with pytest.raises(
            ValueError, match="No BedrockModel found for value: claude 3.5 haiku"
        ):
            BedrockModel.get_by_value("claude 3.5 haiku")

    def test_get_by_value_empty_input(self):
        """
        Test that get_by_value raises a ValueError when given an empty string.
        """
        with pytest.raises(ValueError, match="No BedrockModel found for value:"):
            BedrockModel.get_by_value("")

    def test_get_by_value_incorrect_type(self):
        """
        Test that get_by_value raises a ValueError when given an incorrect input type.
        """
        with pytest.raises(ValueError):
            BedrockModel.get_by_value(123)

    def test_get_by_value_none_input(self):
        """
        Test that get_by_value raises a ValueError when given None as input.
        """
        with pytest.raises(ValueError):
            BedrockModel.get_by_value(None)

    def test_get_by_value_nonexistent_model(self):
        """
        Test that get_by_value raises a ValueError when given a non-existent model name.
        """
        with pytest.raises(
            ValueError, match="No BedrockModel found for value: NonExistentModel"
        ):
            BedrockModel.get_by_value("NonExistentModel")

    def test_get_by_value_raises_value_error_for_invalid_value(self):
        """
        Test that get_by_value raises a ValueError for an invalid display name.
        """
        with pytest.raises(ValueError) as exc_info:
            BedrockModel.get_by_value("Invalid Model Name")
        assert (
            str(exc_info.value) == "No BedrockModel found for value: Invalid Model Name"
        )

    def test_get_by_value_returns_correct_model(self):
        """
        Test that get_by_value returns the correct BedrockModel for a given display name.
        """
        model = BedrockModel.get_by_value("Claude 3.5 Haiku")
        assert model == BedrockModel.ANTHROPIC_HAIKU_3_5
        assert model.model_id == "anthropic.claude-3-5-haiku-20241022-v1:0"
        assert model.inference_profile == "us.anthropic.claude-3-5-haiku-20241022-v1:0"

    def test_get_by_value_whitespace(self):
        """
        Test that get_by_value raises a ValueError when given input with extra whitespace.
        """
        with pytest.raises(
            ValueError, match="No BedrockModel found for value:  Claude 3.5 Haiku "
        ):
            BedrockModel.get_by_value(" Claude 3.5 Haiku ")

    def test_list_does_not_return_inference_profiles(self):
        """
        Test that the list method does not return inference profiles.
        """
        result = BedrockModel.list()
        assert all("us.anthropic" not in item for item in result)

    def test_list_does_not_return_model_ids(self):
        """
        Test that the list method does not return model IDs.
        """
        result = BedrockModel.list()
        assert all("anthropic" not in item for item in result)

    def test_list_returns_all_model_display_names(self):
        """
        Test that the list method returns a list of all model display names.
        """
        expected_names = ["Claude 3.5 Haiku", "Claude 3.5 Sonnet v2"]
        assert BedrockModel.list() == expected_names

    def test_list_returns_correct_display_names(self):
        """
        Test that the list method returns the correct display names for all models.
        """
        expected_names = ["Claude 3.5 Haiku", "Claude 3.5 Sonnet v2"]
        result = BedrockModel.list()
        assert set(result) == set(expected_names)

    def test_list_returns_non_empty_list(self):
        """
        Test that the list method returns a non-empty list of model display names.
        """
        result = BedrockModel.list()
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(item, str) for item in result)
