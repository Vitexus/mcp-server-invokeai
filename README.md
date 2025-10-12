# InvokeAI MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that integrates InvokeAI with Claude Code, enabling AI-powered image generation, transformation, and upscaling directly from your AI assistant.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This MCP server provides a seamless bridge between Claude Code and your local InvokeAI instance, enabling powerful image generation workflows without leaving your development environment. Perfect for creating logos, icons, illustrations, and other visual assets for your projects.

## Features

- **Text-to-Image Generation**: Create images from natural language descriptions
- **Image-to-Image Transformation**: Refine, modify, or stylize existing images
- **LoRA Support**: Apply fine-tuned LoRA models for specialized styles (logos, illustrations, etc.)
- **Full SDXL Support**: Automatic detection and proper configuration for SDXL models with dual CLIP encoders
- **VAE Override Support**: Use external VAE models to fix incompatible built-in VAEs or optimize for specific use cases
- **AI-Powered Upscaling**: Enhance images to higher resolutions (2x-4x) using state-of-the-art Spandrel models
- **Flexible Model Support**: Compatible with Stable Diffusion 1.5, SDXL, and custom fine-tuned models
- **Comprehensive Parameter Control**: Fine-tune generation with width, height, steps, CFG scale, schedulers, and seeds
- **Queue Management**: Monitor and track InvokeAI processing status

## Prerequisites

- **InvokeAI**: A running instance (v4.0+) accessible at `http://127.0.0.1:9090` (or custom URL)
- **Claude Code**: Anthropic's Claude CLI tool installed and configured
- **Python**: Version 3.8 or higher
- **Hardware**: GPU with sufficient VRAM for your chosen models (see [Model Requirements](#model-requirements))

## Installation

### Option 1: Install from PyPI (Recommended)

The easiest way to install the InvokeAI MCP server:

```bash
pip install invokeai-mcp-server
```

Then register with Claude Code:

```bash
# Linux/macOS/WSL
claude mcp add --scope user invokeai python -m invokeai_mcp_server

# Windows
claude mcp add --scope user invokeai python -m invokeai_mcp_server
```

### Option 2: Install via Smithery

Install using the Smithery CLI for automatic configuration:

```bash
npx @smithery/cli install invokeai --client claude
```

### Option 3: Install from Source

For development or customization:

```bash
# Clone the repository
git clone https://github.com/coinstax/invokeai-mcp-server.git
cd invokeai-mcp-server

# Run the automated setup script
./setup.sh
```

**Or manually:**

```bash
# Clone the repository
git clone https://github.com/coinstax/invokeai-mcp-server.git
cd invokeai-mcp-server

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### For Source Installation Only

If you installed from source, register with Claude Code:

**Linux/WSL/macOS:**
```bash
claude mcp add --scope user invokeai \
  ~/invokeai-mcp-server/venv/bin/python \
  ~/invokeai-mcp-server/invokeai_mcp_server.py
```

**Windows:**
```bash
claude mcp add --scope user invokeai ^
  C:\path\to\invokeai-mcp-server\venv\Scripts\python.exe ^
  C:\path\to\invokeai-mcp-server\invokeai_mcp_server.py
```

### Verify Installation

```bash
claude mcp list
```

Expected output:
```
invokeai: ... - ✓ Connected
```

After registration, restart Claude Code or start a new conversation to access the tools.

## Usage

### Available Tools

#### `generate_image`
Generate images from text prompts with optional LoRA support.

**Parameters:**
- `prompt` (string, required): Description of the image to generate
- `negative_prompt` (string, optional): Elements to avoid in the generation
- `width` (integer, optional, default: 512): Image width (64-2048px)
- `height` (integer, optional, default: 512): Image height (64-2048px)
- `steps` (integer, optional, default: 30): Denoising steps (1-150)
- `cfg_scale` (float, optional, default: 7.5): Guidance scale (1.0-20.0)
- `scheduler` (string, optional, default: "euler"): Sampling scheduler
- `seed` (integer, optional): Random seed for reproducibility
- `model_key` (string, optional): Specific model identifier
- `lora_key` (string, optional): LoRA model identifier for fine-tuned style control
- `lora_weight` (float, optional, default: 1.0): LoRA strength (0.0-2.0)
- `vae_key` (string, optional): VAE model identifier to override model's built-in VAE

**Example:**
```
Generate a minimalist tech logo with blue and white colors, geometric shapes, flat design
```

**Example with LoRA:**
```
Generate a professional logo using the logomkrdsxl LoRA with prompt: "tech startup logo, modern, clean"
```

#### `img2img`
Transform existing images using text guidance with optional LoRA support.

**Parameters:**
- `image_path` (string, required): Path to source image or `image_name` from previous generation
- `prompt` (string, required): Description of desired transformation
- `negative_prompt` (string, optional): Elements to avoid
- `strength` (float, optional, default: 0.75): Transformation strength (0.0-1.0)
- `steps` (integer, optional, default: 30): Denoising steps (1-150)
- `cfg_scale` (float, optional, default: 7.5): Guidance scale (1.0-20.0)
- `scheduler` (string, optional, default: "euler"): Sampling scheduler
- `seed` (integer, optional): Random seed for reproducibility
- `model_key` (string, optional): Specific model identifier
- `lora_key` (string, optional): LoRA model identifier for fine-tuned style control
- `lora_weight` (float, optional, default: 1.0): LoRA strength (0.0-2.0)
- `vae_key` (string, optional): VAE model identifier to override model's built-in VAE

**Example:**
```
Refine this logo with strength 0.6: /path/to/sketch.png
Prompt: professional polished logo, clean lines, modern aesthetic
```

**Example with LoRA:**
```
Transform logo.png with logomkrdsxl LoRA at strength 0.6 to make it more professional
```

#### `upscale_image`
Enhance image resolution using AI upscaling.

**Parameters:**
- `image_path` (string, required): Path to image or `image_name` from previous generation
- `model_key` (string, optional): Specific upscaling model (auto-selects if omitted)

**Example:**
```
Upscale this image to high resolution: generated_logo.png
```

#### `list_models`
List available models in your InvokeAI instance.

**Parameters:**
- `model_type` (string, optional, default: "main"): Model type (main, vae, lora, controlnet, embedding, spandrel_image_to_image)

**Example:**
```
List all available SDXL models
```

#### `get_queue_status`
Check InvokeAI processing queue status.

**Parameters:**
- `queue_id` (string, optional, default: "default"): Queue identifier

## Model Requirements

### VRAM Requirements

| Model Type | Minimum VRAM | Recommended VRAM | Notes |
|------------|--------------|------------------|-------|
| SD 1.5 | 4GB | 6-8GB | Faster generation, good for iteration |
| SDXL | 8GB | 12GB+ | Higher quality, slower generation |
| Upscaling (Spandrel) | 4GB | 6GB+ | Depends on source image resolution |

### Recommended Models

#### Base Models

**Stable Diffusion XL (SDXL)**
- Superior quality for detailed graphics and illustrations
- Better text rendering capabilities
- Ideal for final production assets
- Download from: [Stability AI on HuggingFace](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0)

**Stable Diffusion 1.5**
- Faster generation for rapid prototyping
- Lower VRAM requirements
- Recommended: [Dreamshaper](https://civitai.com/models/4384/dreamshaper), [Realistic Vision](https://civitai.com/models/4201/realistic-vision)

#### Specialized Models (LoRAs)

- **Vector Illustration LoRA** - Clean vector-style graphics
- **Logo Maker 9000 SDXL** - Purpose-built for logo generation
- **Flat Design LoRAs** - Modern UI/UX style illustrations

Model repositories:
- [Civitai](https://civitai.com/) - Community models and LoRAs
- [HuggingFace](https://huggingface.co/) - Official Stability AI models

> **Note:** FLUX models use a different architecture and may have limited compatibility with InvokeAI's workflow system. For best results, use SD 1.5 or SDXL-based models.

## Workflow Examples

### Logo Design Pipeline
```
1. Generate initial concept with LoRA (512x512, 25 steps, logomkrdsxl LoRA)
2. Refine with img2img + LoRA (strength 0.6-0.7)
3. Upscale to high resolution (4x)
4. Export final asset
```

### LoRA Workflow
```
1. List available LoRAs: list_models(model_type="lora")
2. Generate with LoRA: generate_image(prompt="...", lora_key="...", lora_weight=1.0)
3. Experiment with weights: Try 0.5 (subtle), 1.0 (standard), 1.5 (strong)
4. Combine with img2img for iterative refinement
```

### Rapid Prototyping
```
1. Generate variations (SD 1.5 for speed)
2. Select best candidate
3. Upscale to production resolution
4. Apply final refinements with img2img
```

## Architecture

The server implements a graph-based workflow system that interfaces with InvokeAI's node architecture:

1. **Model Loading** - Initializes selected SD model and VAE
2. **Prompt Encoding** - Processes positive and negative prompts via CLIP
3. **Latent Generation** - Creates noise tensors with specified dimensions
4. **Denoising** - Iteratively refines latents using the diffusion process
5. **Decoding** - Converts latents to pixel space via VAE
6. **Output** - Saves final image to InvokeAI's storage

All workflows are automatically constructed and managed by the server based on the requested operation.

## Troubleshooting

### Server Not Connecting

**Symptoms:** MCP server doesn't appear in Claude Code tools list

**Solutions:**
1. Verify InvokeAI is running: `curl http://127.0.0.1:9090/api/v1/app/version`
2. Check server registration: `claude mcp list`
3. Restart Claude Code or start a new conversation
4. Check Python dependencies: `pip install -r requirements.txt`

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection refused | InvokeAI not running | Start InvokeAI service |
| No models available | Models not installed | Install models via InvokeAI Model Manager |
| Import errors | Missing dependencies | Run `pip install -r requirements.txt` |
| Generation fails | Insufficient VRAM | Reduce image size or use SD 1.5 |
| Upscaling fails | No Spandrel models | Install upscaling models in InvokeAI |
| SDXL + LoRA issues | Model incompatibility | Ensure LoRA base type matches SDXL model |
| Black images (SDXL) | Corrupt/missing VAE | Use VAE override: `vae_key: "sdxl.vae"` or `vae_key: "sdxl-vae-fp16-fix"` |

### Uninstalling

**If installed via PyPI:**
```bash
pip uninstall invokeai-mcp-server
claude mcp remove invokeai
```

**If installed via Smithery:**
```bash
smithery uninstall invokeai --client claude
```

**If installed from source:**
```bash
claude mcp remove invokeai
```

## Development

### Testing

Test the server directly:
```bash
python3 invokeai_mcp_server.py
```

The server will start in stdio mode, waiting for MCP protocol messages.

### Project Structure

```
invokeai-mcp-server/
├── invokeai_mcp_server.py    # Main server implementation
├── requirements.txt           # Python dependencies
├── setup.sh                   # Automated setup script
├── README.md                  # Documentation
└── LICENSE                    # MIT License
```

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on the [Model Context Protocol](https://modelcontextprotocol.io)
- Powered by [InvokeAI](https://github.com/invoke-ai/InvokeAI)
- Integrated with [Claude Code](https://claude.ai/claude-code)

## Links

- **Repository**: https://github.com/coinstax/invokeai-mcp-server
- **InvokeAI**: https://github.com/invoke-ai/InvokeAI
- **Model Context Protocol**: https://modelcontextprotocol.io
- **Issues**: https://github.com/coinstax/invokeai-mcp-server/issues
