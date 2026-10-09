from stage7_llm_generator.llm_generator import LLMGenerator

try:
    import boto3
except ImportError as exc:
    raise ImportError(
        "boto3 is required for NovaLiteGenerator. "
        "Install it with 'pip install boto3'."
    ) from exc


class NovaLiteGenerator(LLMGenerator):
    def __init__(
        self,
        region_name: str = "us-east-1",
        model_id: str = "us.amazon.nova-lite-v1:0",
        max_tokens: int = 512,
        temperature: float = 0.2,
        top_p: float = 0.9
    ):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=region_name
        )

        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p

    def generate(self, prompt: str) -> str:
        response = self.client.converse(
            modelId=self.model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            inferenceConfig={
                "maxTokens": self.max_tokens,
                "temperature": self.temperature,
                "topP": self.top_p
            }
        )

        answer = response["output"]["message"]["content"][0]["text"]
        return answer