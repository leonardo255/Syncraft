from dotenv import load_dotenv
from langchain.chat_models import init_chat_model


load_dotenv()

gpt_5_nano = init_chat_model(
    "openai:gpt-5-nano",
    temperature=0.5,
    timeout=30,
    max_tokens=5000,
)

mistral_3_8B = init_chat_model(
    "mistral-small-latest",
    temperature=0.5,
    timeout=30,
    max_tokens=5000,
)

anthropic = init_chat_model(
    "anthropic:claude-haiku-4-5",
    temperature=0.5,
    timeout=30,
    max_tokens=5000,
)

LLM_MODEL = anthropic