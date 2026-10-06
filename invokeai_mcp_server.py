#!/usr/bin/env python3
"""
InvokeAI MCP Server
Provides tools for image generation using a local InvokeAI instance.
"""

import asyncio
import json
import logging
import os
from typing import Annotated, Any, Literal, Optional
from urllib.parse import urljoin

import httpx
from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("invokeai-mcp")

# InvokeAI API configuration
INVOKEAI_BASE_URL = os.environ.get("INVOKEAI_BASE_URL", "http://127.0.0.1:9090")
READ_ONLY = os.environ.get("INVOKEAI_READ_ONLY", "").lower() in ("1", "true", "yes")
DEFAULT_QUEUE_ID = "default"

# Initialize MCP server
mcp = FastMCP("invokeai")

READ_ONLY_ANNOTATIONS = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True)
CREATE_ANNOTATIONS = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True)

# HTTP client
http_client: Optional[httpx.AsyncClient] = None


def get_client() -> httpx.AsyncClient:
    """Get or create HTTP client."""
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(base_url=INVOKEAI_BASE_URL, timeout=120.0)
    return http_client


async def enqueue_graph(graph: dict, queue_id: str = DEFAULT_QUEUE_ID) -> dict:
    """Enqueue a graph for processing."""
    client = get_client()

    batch = {
        "batch": {
            "graph": graph,
            "runs": 1,
            "data": None
        }
    }

    response = await client.post(
        f"/api/v1/queue/{queue_id}/enqueue_batch",
        json=batch
    )
    response.raise_for_status()
    return response.json()


async def wait_for_completion(batch_id: str, queue_id: str = DEFAULT_QUEUE_ID, timeout: int = 300) -> dict:
    """Wait for a batch to complete and return the most recent image."""
    client = get_client()
    start_time = asyncio.get_event_loop().time()

    while True:
        # Check if we've exceeded timeout
        if asyncio.get_event_loop().time() - start_time > timeout:
            raise TimeoutError(f"Image generation timed out after {timeout} seconds")

        # Get batch status
        response = await client.get(f"/api/v1/queue/{queue_id}/b/{batch_id}/status")
        response.raise_for_status()
        status_data = response.json()

        # Check for failures
        failed_count = status_data.get("failed", 0)
        if failed_count > 0:
            # Try to get error details from the queue
            queue_status_response = await client.get(f"/api/v1/queue/{queue_id}/status")
            queue_status_response.raise_for_status()
            queue_data = queue_status_response.json()

            raise RuntimeError(
                f"Image generation failed. Batch {batch_id} has {failed_count} failed item(s). "
                f"Queue status: {json.dumps(queue_data, indent=2)}"
            )

        # Check completion
        completed = status_data.get("completed", 0)
        total = status_data.get("total", 0)

        if completed == total and total > 0:
            # Get most recent non-intermediate image
            images_response = await client.get("/api/v1/images/?is_intermediate=false&limit=10")
            images_response.raise_for_status()
            images_data = images_response.json()

            # Return the most recent image (first in the list)
            if images_data.get("items"):
                return {
                    "batch_id": batch_id,
                    "status": "completed",
                    "result": {
                        "outputs": {
                            "save_image": {
                                "type": "image_output",
                                "image": {
                                    "image_name": images_data["items"][0]["image_name"]
                                }
                            }
                        }
                    }
                }

            # If no images found, return status
            return status_data

        # Wait before checking again
        await asyncio.sleep(1)


async def get_image_url(image_name: str) -> str:
    """Get the URL for an image."""
    client = get_client()
    response = await client.get(f"/api/v1/images/i/{image_name}/urls")
    response.raise_for_status()
    data = response.json()
    return data.get("image_url", "")


async def upload_image(image_path: str) -> str:
    """Upload an image file and return its image_name."""
    import os
    client = get_client()

    if not os.path.exists(image_path):
        raise ValueError(f"Image file not found: {image_path}")

    with open(image_path, 'rb') as f:
        files = {'file': (os.path.basename(image_path), f, 'image/png')}
        response = await client.post("/api/v1/images/uploads", files=files)
        response.raise_for_status()
        data = response.json()
        return data["image_name"]


async def list_models(model_type: str = "main") -> list:
    """List available models."""
    client = get_client()
    response = await client.get("/api/v2/models/", params={"model_type": model_type})
    response.raise_for_status()
    data = response.json()
    return data.get("models", [])


async def get_model_info(model_key: str) -> Optional[dict]:
    """Get information about a specific model."""
    client = get_client()
    try:
        response = await client.get(f"/api/v2/models/i/{model_key}")
        response.raise_for_status()
        model_data = response.json()

        # Ensure we have a valid dictionary
        if not isinstance(model_data, dict):
            logger.error(f"Model info for {model_key} is not a dictionary: {type(model_data)}")
            return None

        return model_data
    except Exception as e:
        logger.error(f"Error fetching model info for {model_key}: {e}")
        return None


async def create_text2img_graph(
    prompt: str,
    negative_prompt: str = "",
    model_key: Optional[str] = None,
    lora_key: Optional[str] = None,
    lora_weight: float = 1.0,
    vae_key: Optional[str] = None,
    width: int = 512,
    height: int = 512,
    steps: int = 30,
    cfg_scale: float = 7.5,
    scheduler: str = "euler",
    seed: Optional[int] = None
) -> dict:
    """Create a text-to-image generation graph with optional LoRA and VAE support."""

    # Use default model if not specified
    if model_key is None:
        # Try to find an sd-1 model
        models = await list_models("main")
        for model in models:
            if model.get("base") == "sd-1":
                model_key = model["key"]
                break
        if model_key is None:
            raise ValueError("No suitable model found")

    # Get model information
    model_info = await get_model_info(model_key)
    if not model_info:
        raise ValueError(f"Model {model_key} not found")

    # Validate model info has required fields
    if not isinstance(model_info, dict):
        raise ValueError(f"Model {model_key} returned invalid data type: {type(model_info)}")

    required_fields = ["key", "hash", "name", "base", "type"]
    for field in required_fields:
        if field not in model_info or model_info[field] is None:
            raise ValueError(f"Model {model_key} is missing required field: {field}")

    # Generate random seed if not provided
    if seed is None:
        import random
        seed = random.randint(0, 2**32 - 1)

    # Detect if this is an SDXL model
    is_sdxl = model_info["base"] == "sdxl"

    # Build nodes dictionary
    nodes = {
        # Main model loader - use sdxl_model_loader for SDXL models
        "model_loader": {
            "type": "sdxl_model_loader" if is_sdxl else "main_model_loader",
            "id": "model_loader",
            "model": {
                "key": model_info["key"],
                "hash": model_info["hash"],
                "name": model_info["name"],
                "base": model_info["base"],
                "type": model_info["type"]
            }
        },

        # Positive prompt encoding - use sdxl_compel_prompt for SDXL
        "positive_prompt": {
            "type": "sdxl_compel_prompt" if is_sdxl else "compel",
            "id": "positive_prompt",
            "prompt": prompt,
            **({"style": prompt} if is_sdxl else {})
        },

        # Negative prompt encoding - use sdxl_compel_prompt for SDXL
        "negative_prompt": {
            "type": "sdxl_compel_prompt" if is_sdxl else "compel",
            "id": "negative_prompt",
            "prompt": negative_prompt,
            **({"style": ""} if is_sdxl else {})
        },

        # Noise generation
        "noise": {
            "type": "noise",
            "id": "noise",
            "seed": seed,
            "width": width,
            "height": height,
            "use_cpu": False
        },

        # Denoise latents (main generation step)
        "denoise": {
            "type": "denoise_latents",
            "id": "denoise",
            "steps": steps,
            "cfg_scale": cfg_scale,
            "scheduler": scheduler,
            "denoising_start": 0,
            "denoising_end": 1
        },

        # Convert latents to image
        "latents_to_image": {
            "type": "l2i",
            "id": "latents_to_image"
        },

        # Save image
        "save_image": {
            "type": "save_image",
            "id": "save_image",
            "is_intermediate": False
        }
    }

    # Add LoRA loader if requested
    if lora_key is not None:
        lora_info = await get_model_info(lora_key)
        if not lora_info:
            raise ValueError(f"LoRA model {lora_key} not found")

        # Validate LoRA info has required fields
        required_fields = ["key", "hash", "name", "base", "type"]
        for field in required_fields:
            if field not in lora_info or lora_info[field] is None:
                raise ValueError(f"LoRA model {lora_key} is missing required field: {field}")

        nodes["lora_loader"] = {
            "type": "lora_loader",
            "id": "lora_loader",
            "lora": {
                "key": lora_info["key"],
                "hash": lora_info["hash"],
                "name": lora_info["name"],
                "base": lora_info["base"],
                "type": lora_info["type"]
            },
            "weight": lora_weight
        }

    # Add VAE loader if requested (to override model's built-in VAE)
    if vae_key is not None:
        vae_info = await get_model_info(vae_key)
        if not vae_info:
            raise ValueError(f"VAE model {vae_key} not found")

        # Validate VAE info has required fields
        required_fields = ["key", "hash", "name", "base", "type"]
        for field in required_fields:
            if field not in vae_info or vae_info[field] is None:
                raise ValueError(f"VAE model {vae_key} is missing required field: {field}")

        nodes["vae_loader"] = {
            "type": "vae_loader",
            "id": "vae_loader",
            "vae_model": {
                "key": vae_info["key"],
                "hash": vae_info["hash"],
                "name": vae_info["name"],
                "base": vae_info["base"],
                "type": vae_info["type"]
            }
        }

    # Build edges
    edges = []

    # Determine source for UNet and CLIP (model_loader or lora_loader)
    unet_source = "lora_loader" if lora_key is not None else "model_loader"
    clip_source = "lora_loader" if lora_key is not None else "model_loader"
    # Determine source for VAE (vae_loader if specified, otherwise model_loader)
    vae_source = "vae_loader" if vae_key is not None else "model_loader"

    # If using LoRA, connect model_loader to lora_loader first
    if lora_key is not None:
        edges.extend([
            {
                "source": {"node_id": "model_loader", "field": "unet"},
                "destination": {"node_id": "lora_loader", "field": "unet"}
            },
            {
                "source": {"node_id": "model_loader", "field": "clip"},
                "destination": {"node_id": "lora_loader", "field": "clip"}
            }
        ])
        # Note: lora_loader doesn't have a clip2 field, so for SDXL we route clip2 directly from model_loader

    # Connect UNet and CLIP to downstream nodes
    edges.extend([
        # Connect UNet to denoise
        {
            "source": {"node_id": unet_source, "field": "unet"},
            "destination": {"node_id": "denoise", "field": "unet"}
        },
        # Connect CLIP to prompts
        {
            "source": {"node_id": clip_source, "field": "clip"},
            "destination": {"node_id": "positive_prompt", "field": "clip"}
        },
        {
            "source": {"node_id": clip_source, "field": "clip"},
            "destination": {"node_id": "negative_prompt", "field": "clip"}
        },
    ])

    # For SDXL models, also connect clip2
    # Note: clip2 always comes from model_loader, even when using LoRA (lora_loader doesn't support clip2)
    if is_sdxl:
        edges.extend([
            {
                "source": {"node_id": "model_loader", "field": "clip2"},
                "destination": {"node_id": "positive_prompt", "field": "clip2"}
            },
            {
                "source": {"node_id": "model_loader", "field": "clip2"},
                "destination": {"node_id": "negative_prompt", "field": "clip2"}
            },
        ])

    edges.extend([

        # Connect prompts to denoise
        {
            "source": {"node_id": "positive_prompt", "field": "conditioning"},
            "destination": {"node_id": "denoise", "field": "positive_conditioning"}
        },
        {
            "source": {"node_id": "negative_prompt", "field": "conditioning"},
            "destination": {"node_id": "denoise", "field": "negative_conditioning"}
        },

        # Connect noise to denoise
        {
            "source": {"node_id": "noise", "field": "noise"},
            "destination": {"node_id": "denoise", "field": "noise"}
        },

        # Connect denoise to latents_to_image
        {
            "source": {"node_id": "denoise", "field": "latents"},
            "destination": {"node_id": "latents_to_image", "field": "latents"}
        },
        {
            "source": {"node_id": vae_source, "field": "vae"},
            "destination": {"node_id": "latents_to_image", "field": "vae"}
        },

        # Connect latents_to_image to save_image
        {
            "source": {"node_id": "latents_to_image", "field": "image"},
            "destination": {"node_id": "save_image", "field": "image"}
        }
    ])

    graph = {
        "id": "text2img_graph",
        "nodes": nodes,
        "edges": edges
    }

    return graph


async def create_img2img_graph(
    image_name: str,
    prompt: str,
    negative_prompt: str = "",
    strength: float = 0.75,
    model_key: Optional[str] = None,
    lora_key: Optional[str] = None,
    lora_weight: float = 1.0,
    vae_key: Optional[str] = None,
    steps: int = 30,
    cfg_scale: float = 7.5,
    scheduler: str = "euler",
    seed: Optional[int] = None
) -> dict:
    """Create an image-to-image generation graph with optional LoRA and VAE support."""

    # Use default model if not specified
    if model_key is None:
        models = await list_models("main")
        for model in models:
            if model.get("base") == "sd-1":
                model_key = model["key"]
                break
        if model_key is None:
            raise ValueError("No suitable model found")

    # Get model information
    model_info = await get_model_info(model_key)
    if not model_info:
        raise ValueError(f"Model {model_key} not found")

    # Validate model info has required fields
    if not isinstance(model_info, dict):
        raise ValueError(f"Model {model_key} returned invalid data type: {type(model_info)}")

    required_fields = ["key", "hash", "name", "base", "type"]
    for field in required_fields:
        if field not in model_info or model_info[field] is None:
            raise ValueError(f"Model {model_key} is missing required field: {field}")

    # Generate random seed if not provided
    if seed is None:
        import random
        seed = random.randint(0, 2**32 - 1)

    # Calculate denoising range based on strength
    # strength of 1.0 = full denoising (like text2img)
    # strength of 0.0 = no denoising (returns original)
    denoising_start = 1.0 - strength
    denoising_end = 1.0

    # Detect if this is an SDXL model
    is_sdxl = model_info["base"] == "sdxl"

    # Build nodes dictionary
    nodes = {
        # Image to latents - convert input image
        "image_to_latents": {
            "type": "i2l",
            "id": "image_to_latents",
            "image": {
                "image_name": image_name
            }
        },

        # Main model loader - use sdxl_model_loader for SDXL models
        "model_loader": {
            "type": "sdxl_model_loader" if is_sdxl else "main_model_loader",
            "id": "model_loader",
            "model": {
                "key": model_info["key"],
                "hash": model_info["hash"],
                "name": model_info["name"],
                "base": model_info["base"],
                "type": model_info["type"]
            }
        },

        # Positive prompt encoding - use sdxl_compel_prompt for SDXL
        "positive_prompt": {
            "type": "sdxl_compel_prompt" if is_sdxl else "compel",
            "id": "positive_prompt",
            "prompt": prompt,
            **({"style": prompt} if is_sdxl else {})
        },

        # Negative prompt encoding - use sdxl_compel_prompt for SDXL
        "negative_prompt": {
            "type": "sdxl_compel_prompt" if is_sdxl else "compel",
            "id": "negative_prompt",
            "prompt": negative_prompt,
            **({"style": ""} if is_sdxl else {})
        },

        # Noise generation
        "noise": {
            "type": "noise",
            "id": "noise",
            "seed": seed,
            "use_cpu": False
        },

        # Denoise latents (transformation step)
        "denoise": {
            "type": "denoise_latents",
            "id": "denoise",
            "steps": steps,
            "cfg_scale": cfg_scale,
            "scheduler": scheduler,
            "denoising_start": denoising_start,
            "denoising_end": denoising_end
        },

        # Convert latents to image
        "latents_to_image": {
            "type": "l2i",
            "id": "latents_to_image"
        },

        # Save image
        "save_image": {
            "type": "save_image",
            "id": "save_image",
            "is_intermediate": False
        }
    }

    # Add LoRA loader if requested
    if lora_key is not None:
        lora_info = await get_model_info(lora_key)
        if not lora_info:
            raise ValueError(f"LoRA model {lora_key} not found")

        # Validate LoRA info has required fields
        required_fields = ["key", "hash", "name", "base", "type"]
        for field in required_fields:
            if field not in lora_info or lora_info[field] is None:
                raise ValueError(f"LoRA model {lora_key} is missing required field: {field}")

        nodes["lora_loader"] = {
            "type": "lora_loader",
            "id": "lora_loader",
            "lora": {
                "key": lora_info["key"],
                "hash": lora_info["hash"],
                "name": lora_info["name"],
                "base": lora_info["base"],
                "type": lora_info["type"]
            },
            "weight": lora_weight
        }

    # Add VAE loader if requested (to override model's built-in VAE)
    if vae_key is not None:
        vae_info = await get_model_info(vae_key)
        if not vae_info:
            raise ValueError(f"VAE model {vae_key} not found")

        # Validate VAE info has required fields
        required_fields = ["key", "hash", "name", "base", "type"]
        for field in required_fields:
            if field not in vae_info or vae_info[field] is None:
                raise ValueError(f"VAE model {vae_key} is missing required field: {field}")

        nodes["vae_loader"] = {
            "type": "vae_loader",
            "id": "vae_loader",
            "vae_model": {
                "key": vae_info["key"],
                "hash": vae_info["hash"],
                "name": vae_info["name"],
                "base": vae_info["base"],
                "type": vae_info["type"]
            }
        }

    # Build edges
    edges = []

    # Determine source for UNet and CLIP (model_loader or lora_loader)
    unet_source = "lora_loader" if lora_key is not None else "model_loader"
    clip_source = "lora_loader" if lora_key is not None else "model_loader"
    # Determine source for VAE (vae_loader if specified, otherwise model_loader)
    vae_source = "vae_loader" if vae_key is not None else "model_loader"

    # If using LoRA, connect model_loader to lora_loader first
    if lora_key is not None:
        edges.extend([
            {
                "source": {"node_id": "model_loader", "field": "unet"},
                "destination": {"node_id": "lora_loader", "field": "unet"}
            },
            {
                "source": {"node_id": "model_loader", "field": "clip"},
                "destination": {"node_id": "lora_loader", "field": "clip"}
            }
        ])
        # Note: lora_loader doesn't have a clip2 field, so for SDXL we route clip2 directly from model_loader

    # Connect image_to_latents edges
    edges.extend([
        # Connect image_to_latents to denoise (provides starting latents)
        {
            "source": {"node_id": "image_to_latents", "field": "latents"},
            "destination": {"node_id": "denoise", "field": "latents"}
        },
        {
            "source": {"node_id": "image_to_latents", "field": "width"},
            "destination": {"node_id": "noise", "field": "width"}
        },
        {
            "source": {"node_id": "image_to_latents", "field": "height"},
            "destination": {"node_id": "noise", "field": "height"}
        },

        # Connect UNet to denoise
        {
            "source": {"node_id": unet_source, "field": "unet"},
            "destination": {"node_id": "denoise", "field": "unet"}
        },
        # Connect CLIP to prompts
        {
            "source": {"node_id": clip_source, "field": "clip"},
            "destination": {"node_id": "positive_prompt", "field": "clip"}
        },
        {
            "source": {"node_id": clip_source, "field": "clip"},
            "destination": {"node_id": "negative_prompt", "field": "clip"}
        },
    ])

    # For SDXL models, also connect clip2
    # Note: clip2 always comes from model_loader, even when using LoRA (lora_loader doesn't support clip2)
    if is_sdxl:
        edges.extend([
            {
                "source": {"node_id": "model_loader", "field": "clip2"},
                "destination": {"node_id": "positive_prompt", "field": "clip2"}
            },
            {
                "source": {"node_id": "model_loader", "field": "clip2"},
                "destination": {"node_id": "negative_prompt", "field": "clip2"}
            },
        ])

    edges.extend([
        # Connect prompts to denoise
        {
            "source": {"node_id": "positive_prompt", "field": "conditioning"},
            "destination": {"node_id": "denoise", "field": "positive_conditioning"}
        },
        {
            "source": {"node_id": "negative_prompt", "field": "conditioning"},
            "destination": {"node_id": "denoise", "field": "negative_conditioning"}
        },

        # Connect noise to denoise
        {
            "source": {"node_id": "noise", "field": "noise"},
            "destination": {"node_id": "denoise", "field": "noise"}
        },

        # Connect denoise to latents_to_image
        {
            "source": {"node_id": "denoise", "field": "latents"},
            "destination": {"node_id": "latents_to_image", "field": "latents"}
        },
        {
            "source": {"node_id": vae_source, "field": "vae"},
            "destination": {"node_id": "latents_to_image", "field": "vae"}
        },
        {
            "source": {"node_id": "model_loader", "field": "vae"},
            "destination": {"node_id": "image_to_latents", "field": "vae"}
        },

        # Connect latents_to_image to save_image
        {
            "source": {"node_id": "latents_to_image", "field": "image"},
            "destination": {"node_id": "save_image", "field": "image"}
        }
    ])

    graph = {
        "id": "img2img_graph",
        "nodes": nodes,
        "edges": edges
    }

    return graph


async def upscale_image(image_name: str, model_key: Optional[str] = None) -> str:
    """Upscale an image using Spandrel image-to-image models."""
    client = get_client()

    # Get available upscaling models if no model specified
    if model_key is None:
        models = await list_models("spandrel_image_to_image")
        if not models:
            raise ValueError("No upscaling models available")
        model_key = models[0]["key"]  # Use first available model

    # Get model information
    model_info = await get_model_info(model_key)
    if not model_info:
        raise ValueError(f"Upscaling model {model_key} not found")

    # Validate model info has required fields
    required_fields = ["key", "hash", "name", "base", "type"]
    for field in required_fields:
        if field not in model_info or model_info[field] is None:
            raise ValueError(f"Upscaling model {model_key} is missing required field: {field}")

    # Create simple upscaling graph
    graph = {
        "id": "upscale_graph",
        "nodes": {
            "load_image": {
                "type": "image",
                "id": "load_image",
                "image": {"image_name": image_name}
            },
            "upscale": {
                "type": "spandrel_image_to_image",
                "id": "upscale",
                "image_to_image_model": {
                    "key": model_info["key"],
                    "hash": model_info["hash"],
                    "name": model_info["name"],
                    "base": model_info["base"],
                    "type": model_info["type"]
                }
            },
            "save_image": {
                "type": "save_image",
                "id": "save_image",
                "is_intermediate": False
            }
        },
        "edges": [
            {
                "source": {"node_id": "load_image", "field": "image"},
                "destination": {"node_id": "upscale", "field": "image"}
            },
            {
                "source": {"node_id": "upscale", "field": "image"},
                "destination": {"node_id": "save_image", "field": "image"}
            }
        ]
    }

    # Enqueue and wait for completion
    result = await enqueue_graph(graph)
    batch_id = result["batch"]["batch_id"]
    completed = await wait_for_completion(batch_id)

    # Extract image name from result
    if "result" in completed and "outputs" in completed["result"]:
        outputs = completed["result"]["outputs"]
        for node_id, output in outputs.items():
            if output.get("type") == "image_output":
                return output["image"]["image_name"]

    raise ValueError("Upscaling failed: no output image found")


Scheduler = Literal["euler","euler_k","lms","ddim","ddpm","deis","pndm","heun","dpm_2","dpm_2_a","dpmpp_2s","dpmpp_2m","dpmpp_2m_k","dpmpp_sde","dpmpp_sde_k","unipc","lcm"]


def _view_url(image_name: str) -> str:
    return urljoin(INVOKEAI_BASE_URL, f"/api/v1/images/i/{image_name}/full")


async def _run_graph(graph: dict) -> tuple[str, Optional[str]]:
    """Enqueue a graph, wait for it and return (batch_id, output image name)."""
    result = await enqueue_graph(graph)
    batch_id = result["batch"]["batch_id"]
    logger.info(f"Enqueued batch {batch_id}, waiting for completion...")
    completed = await wait_for_completion(batch_id)
    for output in completed.get("result", {}).get("outputs", {}).values():
        if output.get("type") == "image_output":
            return batch_id, output["image"]["image_name"]
    return batch_id, None


async def _resolve_image(image_path: str) -> str:
    """Upload a local file, or pass through an existing InvokeAI image_name."""
    if "/" in image_path or "\\" in image_path:
        logger.info(f"Uploading image from: {image_path}")
        return await upload_image(image_path)
    return image_path


@mcp.tool(
    title="Get Queue Status",
    description="Get the status of the InvokeAI processing queue.",
    annotations=READ_ONLY_ANNOTATIONS,
)
async def get_queue_status(
    queue_id: Annotated[str, Field(description="Queue identifier")] = DEFAULT_QUEUE_ID,
) -> str:
    response = await get_client().get(f"/api/v1/queue/{queue_id}/status")
    response.raise_for_status()
    return f"Queue Status:\n\n{json.dumps(response.json(), indent=2)}"


@mcp.tool(
    name="list_models",
    title="List Models",
    description="List available AI models in InvokeAI.",
    annotations=READ_ONLY_ANNOTATIONS,
)
async def list_models_tool(
    model_type: Annotated[
        Literal["main", "vae", "lora", "controlnet", "embedding", "spandrel_image_to_image"],
        Field(description="Type of models to list"),
    ] = "main",
) -> str:
    models = await list_models(model_type)
    lines = [
        f"- {m.get('name', 'Unknown')} (key: {m.get('key', 'unknown')}, base: {m.get('base', 'unknown')})"
        for m in models
    ]
    return f"Available {model_type} models:\n\n" + "\n".join(lines)


async def generate_image(
    prompt: Annotated[str, Field(description="The text prompt describing the image to generate")],
    negative_prompt: Annotated[str, Field(description="Negative prompt (things to avoid in the image)")] = "",
    width: Annotated[int, Field(description="Image width in pixels", ge=64, le=2048)] = 512,
    height: Annotated[int, Field(description="Image height in pixels", ge=64, le=2048)] = 512,
    steps: Annotated[int, Field(description="Number of denoising steps", ge=1, le=150)] = 30,
    cfg_scale: Annotated[float, Field(description="Classifier-free guidance scale", ge=1.0, le=20.0)] = 7.5,
    scheduler: Annotated[Scheduler, Field(description="Sampling scheduler")] = "euler",
    seed: Annotated[Optional[int], Field(description="Random seed for reproducibility (optional)")] = None,
    model_key: Annotated[Optional[str], Field(description="Model identifier (optional, uses default if not specified)")] = None,
    lora_key: Annotated[Optional[str], Field(description="LoRA model identifier (optional, for fine-tuned style control)")] = None,
    lora_weight: Annotated[float, Field(description="LoRA weight/strength", ge=0.0, le=2.0)] = 1.0,
    vae_key: Annotated[Optional[str], Field(description="VAE model identifier (optional, overrides model's built-in VAE)")] = None,
) -> str:
    logger.info(f"Generating image with prompt: {prompt[:50]}...")
    graph = await create_text2img_graph(
        prompt=prompt, negative_prompt=negative_prompt, model_key=model_key,
        lora_key=lora_key, lora_weight=lora_weight, vae_key=vae_key,
        width=width, height=height, steps=steps, cfg_scale=cfg_scale,
        scheduler=scheduler, seed=seed,
    )
    batch_id, image_name = await _run_graph(graph)
    if image_name is None:
        return f"Image generation completed but output format was unexpected. Batch ID: {batch_id}"
    image_url = await get_image_url(image_name)
    return (
        f"Image generated successfully!\n\nImage Name: {image_name}\nImage URL: {image_url}\n\n"
        f"You can view the image at: {_view_url(image_name)}"
    )


async def img2img(
    image_path: Annotated[str, Field(description="Path to the source image file to transform, OR image_name from a previous generation")],
    prompt: Annotated[str, Field(description="The text prompt describing the desired transformation")],
    negative_prompt: Annotated[str, Field(description="Negative prompt (things to avoid)")] = "",
    strength: Annotated[float, Field(description="How much to transform the image (0.0-1.0). Higher = more changes. Typical: 0.6-0.8", ge=0.0, le=1.0)] = 0.75,
    steps: Annotated[int, Field(description="Number of denoising steps", ge=1, le=150)] = 30,
    cfg_scale: Annotated[float, Field(description="Classifier-free guidance scale", ge=1.0, le=20.0)] = 7.5,
    scheduler: Annotated[Scheduler, Field(description="Sampling scheduler")] = "euler",
    seed: Annotated[Optional[int], Field(description="Random seed for reproducibility (optional)")] = None,
    model_key: Annotated[Optional[str], Field(description="Model identifier (optional, uses default if not specified)")] = None,
    lora_key: Annotated[Optional[str], Field(description="LoRA model identifier (optional, for fine-tuned style control)")] = None,
    lora_weight: Annotated[float, Field(description="LoRA weight/strength", ge=0.0, le=2.0)] = 1.0,
    vae_key: Annotated[Optional[str], Field(description="VAE model identifier (optional, overrides model's built-in VAE)")] = None,
) -> str:
    logger.info(f"Img2img transformation with prompt: {prompt[:50]}...")
    image_name = await _resolve_image(image_path)
    graph = await create_img2img_graph(
        image_name=image_name, prompt=prompt, negative_prompt=negative_prompt,
        strength=strength, model_key=model_key, lora_key=lora_key,
        lora_weight=lora_weight, vae_key=vae_key, steps=steps,
        cfg_scale=cfg_scale, scheduler=scheduler, seed=seed,
    )
    batch_id, result_name = await _run_graph(graph)
    if result_name is None:
        return f"Image transformation completed but output format was unexpected. Batch ID: {batch_id}"
    image_url = await get_image_url(result_name)
    return (
        f"Image transformation completed!\n\nOriginal: {image_name}\nResult: {result_name}\n"
        f"Strength: {strength}\n\nImage URL: {image_url}\n\nView at: {_view_url(result_name)}"
    )


async def upscale_image_tool(
    image_path: Annotated[str, Field(description="Path to the image file to upscale, OR image_name from a previous generation")],
    model_key: Annotated[Optional[str], Field(description="Upscaling model key to use (optional, uses default if not specified)")] = None,
) -> str:
    logger.info(f"Upscaling image: {image_path}")
    image_name = await _resolve_image(image_path)
    upscaled = await upscale_image(image_name, model_key)
    image_url = await get_image_url(upscaled)
    return (
        f"Image upscaled successfully!\n\nOriginal: {image_name}\nUpscaled: {upscaled}\n\n"
        f"Image URL: {image_url}\n\nView at: {_view_url(upscaled)}"
    )


if not READ_ONLY:
    mcp.tool(
        name="generate_image", title="Generate Image",
        description="Generate an image from a text prompt using InvokeAI (enqueues a job and creates a new image). Returns the generated image URL.",
        annotations=CREATE_ANNOTATIONS,
    )(generate_image)
    mcp.tool(
        name="img2img", title="Image to Image",
        description="Transform an existing image using a text prompt (image-to-image generation). Creates a new image; useful for refining, modifying, or stylizing existing images.",
        annotations=CREATE_ANNOTATIONS,
    )(img2img)
    mcp.tool(
        name="upscale_image", title="Upscale Image",
        description="Upscale an image to higher resolution using AI upscaling (typically 2x-4x). Creates a new image.",
        annotations=CREATE_ANNOTATIONS,
    )(upscale_image_tool)

def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
