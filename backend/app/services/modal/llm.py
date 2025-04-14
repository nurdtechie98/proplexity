from modal import Image, App, web_server, concurrent, Volume
from typing import Optional
from openai import OpenAI
import time

# Model configuration
MODEL_NAME = "neuralmagic/Meta-Llama-3.1-8B-Instruct-quantized.w4a16"
MODEL_REVISION = "a7c09948d9a632c2c840722f519672cd94af885d"
MODEL_DIR = "/model"

VLLM_PORT = 8000
API_KEY = "super-secret-key"
# Create Modal app
app = App("llm-service")

hf_cache_vol = Volume.from_name(
    "huggingface-cache", create_if_missing=True
)
vllm_cache_vol = Volume.from_name("vllm-cache", create_if_missing=True)


image = (
    Image.debian_slim(python_version="3.12")
    .pip_install(
        "vllm==0.7.2",
        "huggingface_hub[hf_transfer]==0.26.2",
        "flashinfer-python==0.2.0.post2",  # pinning, very unstable
        extra_index_url="https://flashinfer.ai/whl/cu124/torch2.5",
    )
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "VLLM_USE_V1": "1"
    })
)

GPU_CONFIG = "H100:1"


@app.function(
    image=image,
    gpu=GPU_CONFIG,
    scaledown_window=15 * 60,
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    }
)
@concurrent(max_inputs=100)
@web_server(port=VLLM_PORT, startup_timeout=300)
def serve():
    """Start the vLLM OpenAI-compatible server.

    This function initializes and runs a vLLM server that provides an
    OpenAI-compatible API endpoint. The server:
    - Loads the quantized LLaMA model
    - Serves it efficiently using vLLM
    - Handles concurrent requests
    - Provides auto-scaling capabilities

    The server exposes endpoints compatible with OpenAI's API:
    - /v1/chat/completions for chat completions
    - /v1/completions for text completions

    Environment:
        - Uses H100 GPU for inference
        - Persistent cache volumes for model weights
        - Automatic scaling based on demand
        - 15-minute scale-down window

    Authentication:
        - Uses API key authentication
        - Key must be provided in requests
    """
    import subprocess

    """Start the vLLM OpenAI-compatible server."""
    cmd = [
        "vllm",
        "serve",
        "--uvicorn-log-level=info",
        MODEL_NAME,
        "--revision",
        MODEL_REVISION,
        "--host",
        "0.0.0.0",
        "--port",
        str(VLLM_PORT),
        "--api-key",
        API_KEY,
    ]

    print("Starting vLLM server with command:", " ".join(cmd))
    print("\nOnce deployed, you can use the OpenAI client like this:")

    subprocess.Popen(" ".join(cmd), shell=True)


@app.local_entrypoint()
def main(prompt: Optional[str] = None):
    """Local entrypoint for testing the LLM service.

    This function provides a simple way to test the LLM service locally.
    It creates a test client and sends a sample request to the deployed
    endpoint.

    Args:
        prompt (Optional[str]): The prompt to send to the model.
            If None, uses a default test prompt.

    Example:
        ```bash
        # Test with default prompt
        modal run llm.py

        # Test with custom prompt
        modal run llm.py --prompt "Explain quantum computing"
        ```

    Output:
        Prints the model's response and the time taken for inference.
    """

    # Initialize OpenAI client with our custom endpoint
    client = OpenAI(
        base_url="https://chiragshetty98--llm-service-serve.modal.run/v1",
        api_key="super-secret-key"
    )

    # Test chat completion endpoint
    print("\nTesting chat completion...")
    start_time = time.time()
    chat_completion = client.chat.completions.create(
        model="neuralmagic/Meta-Llama-3.1-8B-Instruct-quantized.w4a16",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.7
    )
    chat_time = time.time() - start_time

    print(f"\nChat Completion (took {chat_time:.2f}s):")
    print(chat_completion.choices[0].message.content)
