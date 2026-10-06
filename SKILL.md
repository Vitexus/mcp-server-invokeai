---
name: invokeai-image-generation
description: Generate, transform and upscale images through a local InvokeAI instance using the mcp-server-invokeai MCP server. Use when a user asks to create an image from a prompt, restyle an existing image (img2img), upscale an image, or check available models and the InvokeAI queue.
---

# InvokeAI Image Generation

Uses the tools of `mcp-server-invokeai` (InvokeAI REST API, default `http://127.0.0.1:9090`).

## Workflow

1. `list_models` (`model_type`: main, vae, lora, controlnet, embedding, spandrel_image_to_image) to find a `model_key` when the user wants a specific model; omit it to use the default.
2. `generate_image` for text-to-image; `img2img` to transform an existing image; `upscale_image` to enlarge one.
3. Results return an `image_name` that can be passed as `image_path` to `img2img`/`upscale_image` to chain steps.
4. `get_queue_status` if a job seems stuck.

## Notes

- Generation can take minutes; start with small sizes/steps (512px, 20-30 steps) when iterating.
- Local file paths must be inside `$HOME`, the temp dir or `INVOKEAI_UPLOAD_ROOT`, and be png/jpg/webp.
- With `INVOKEAI_READ_ONLY=true` only `list_models` and `get_queue_status` exist.
