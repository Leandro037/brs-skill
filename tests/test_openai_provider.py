from types import SimpleNamespace

from brs.providers.openai_responses import OpenAIResponsesProvider


class FakeResponses:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            output_text='{"ok":true}',
            model=kwargs["model"],
            usage=SimpleNamespace(
                input_tokens=12,
                output_tokens=4,
                total_tokens=16,
            ),
        )


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


def test_openai_provider_uses_responses_api_contract():
    client = FakeClient()
    provider = OpenAIResponsesProvider(
        model="test-model",
        client=client,
    )

    result = provider.generate(
        instructions="Return JSON",
        input_text="Create an object",
    )

    assert result.text == '{"ok":true}'
    assert result.model == "test-model"
    assert result.total_tokens == 16
    assert client.responses.calls == [{
        "model": "test-model",
        "instructions": "Return JSON",
        "input": "Create an object",
    }]
