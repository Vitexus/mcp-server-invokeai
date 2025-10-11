# InvokeAI MCP Server

An MCP (Model Context Protocol) server that provides text-to-image generation capabilities using a local InvokeAI instance.

## Features

- **Text-to-Image Generation**: Generate images from text prompts
- **Image-to-Image (img2img)**: Transform existing images with prompts - perfect for refining designs and creating variations
- **AI Upscaling**: Enhance images to higher resolution (2x-4x) using Spandrel models (SwinIR, RealESRGAN, etc.)
- **Model Selection**: Choose from available models (SD 1.5, SDXL, and more)
- **Customizable Parameters**: Control width, height, steps, CFG scale, scheduler, and seed
- **Queue Status**: Check the status of the InvokeAI processing queue

## Installation

### Quick Setup (Recommended)

1. Clone this repository:
```bash
git clone <repository-url>
cd invokeai-mcp-server
```

2. Install python3-venv if needed (Linux/WSL):
```bash
sudo apt install python3-venv
```

3. Run the setup script:
```bash
./setup.sh
```

### Manual Setup

1. Clone this repository:
```bash
git clone <repository-url>
cd invokeai-mcp-server
```

2. Install python3-venv (if not already installed):
```bash
sudo apt install python3-venv  # Linux/WSL
# macOS: python3-venv is included with Python
```

3. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Make sure your InvokeAI instance is running at `http://127.0.0.1:9090`

## Configuration for Claude Code

### Adding the MCP Server

Use the Claude CLI command to register the server (recommended):

```bash
claude mcp add --scope user invokeai /path/to/invokeai-mcp-server/venv/bin/python /path/to/invokeai-mcp-server/invokeai_mcp_server.py
```

**Parameters:**
- `--scope user`: Makes the server available across all projects
- `invokeai`: The server name
- First path: Path to your virtual environment Python interpreter
- Second path: Path to the server script

**Example for Linux/WSL:**
```bash
claude mcp add --scope user invokeai ~/invokeai-mcp-server/venv/bin/python ~/invokeai-mcp-server/invokeai_mcp_server.py
```

**Example for macOS:**
```bash
claude mcp add --scope user invokeai ~/invokeai-mcp-server/venv/bin/python ~/invokeai-mcp-server/invokeai_mcp_server.py
```

**Example for Windows:**
```bash
claude mcp add --scope user invokeai C:\Users\YourName\invokeai-mcp-server\venv\Scripts\python.exe C:\Users\YourName\invokeai-mcp-server\invokeai_mcp_server.py
```

### Verifying the Installation

Check that the server is registered and connected:

```bash
claude mcp list
```

You should see:
```
invokeai: /path/to/invokeai-mcp-server/venv/bin/python /path/to/invokeai-mcp-server/invokeai_mcp_server.py - ✓ Connected
```

### Important Notes

- **Always use the CLI command** rather than manually editing config files
- The server will be registered in `~/.claude.json` (user scope)
- After registration, restart Claude Code or start a new conversation to access the tools
- The command should point to the Python interpreter in your virtual environment

## Usage

Once configured, you can use the following tools in Claude Code:

### generate_image

Generate an image from a text prompt.

**Parameters:**
- `prompt` (required): Text description of the image to generate
- `negative_prompt` (optional): Things to avoid in the image
- `width` (optional, default: 512): Image width in pixels (64-2048)
- `height` (optional, default: 512): Image height in pixels (64-2048)
- `steps` (optional, default: 30): Number of denoising steps (1-150)
- `cfg_scale` (optional, default: 7.5): Classifier-free guidance scale (1.0-20.0)
- `scheduler` (optional, default: "euler"): Sampling scheduler
- `seed` (optional): Random seed for reproducibility
- `model_key` (optional): Model identifier

**Example:**
```
Generate an image of a sunset over mountains
```

### list_models

List available models in your InvokeAI instance.

**Parameters:**
- `model_type` (optional, default: "main"): Type of models to list (main, vae, lora, controlnet, embedding)

### img2img

Transform an existing image using a text prompt (image-to-image generation).

**Parameters:**
- `image_path` (required): Path to the source image file to transform
- `prompt` (required): Text description of the desired transformation
- `negative_prompt` (optional): Things to avoid in the transformation
- `strength` (optional, default: 0.75): How much to transform (0.0-1.0). Higher = more changes. Typical range: 0.6-0.8
- `steps` (optional, default: 30): Number of denoising steps (1-150)
- `cfg_scale` (optional, default: 7.5): Classifier-free guidance scale (1.0-20.0)
- `scheduler` (optional, default: "euler"): Sampling scheduler
- `seed` (optional): Random seed for reproducibility
- `model_key` (optional): Model identifier

**Example:**
```
Transform this sketch into a polished logo using /path/to/sketch.png
```

### upscale_image

Upscale an image to higher resolution using AI upscaling (typically 2x-4x).

**Parameters:**
- `image_path` (required): Path to image file, or image_name from a previous generation
- `model_name` (optional): Upscaling model to use (uses default if not specified)

**Example:**
```
Upscale this image: /path/to/image.png
```

### get_queue_status

Get the status of the InvokeAI processing queue.

**Parameters:**
- `queue_id` (optional, default: "default"): Queue identifier

## Testing

You can test the server directly:

```bash
python3 invokeai_mcp_server.py
```

This will start the server in stdio mode, waiting for MCP protocol messages.

## Troubleshooting

### Server Not Appearing in Claude Code

If the server doesn't appear after registration:
1. Verify registration: `claude mcp list` (should show `✓ Connected`)
2. Restart Claude Code or start a new conversation
3. If issues persist, see [MCP_TROUBLESHOOTING.md](./MCP_TROUBLESHOOTING.md)

### Common Issues

- **InvokeAI not responding**: Make sure InvokeAI is running at `http://127.0.0.1:9090`
- **No models available**: Check that you have models installed in InvokeAI
- **Import errors**: Verify Python dependencies are installed: `pip install -r requirements.txt`
- **Generation fails**: Check the InvokeAI logs for errors

### Removing the Server

If you need to unregister the server:
```bash
claude mcp remove invokeai
```

## Recommended Models for Logo/Website Design

For creating logos, icons, and website illustrations on your RTX 3090 (24GB VRAM), these models work great with InvokeAI:

### Base Models

**SDXL (Stable Diffusion XL)**
- Best overall quality for detailed graphics
- Great for photorealistic and stylized outputs
- Handles text in images better than SD 1.5
- Your 3090 can run SDXL comfortably

**Stable Diffusion 1.5 Models**
- Faster generation than SDXL
- Lower VRAM usage
- Models like "Realistic Vision" work well for professional graphics

### Specialized LoRA Models (Add-ons)

**For Logos & Icons:**
- **Vector Illustration LoRA** (Civitai) - Creates clean vector-style graphics
- **Logo Maker 9000 SDXL** (Civitai) - Specifically trained for logo generation

**For Flat Design:**
- Search Civitai for "flat design" or "minimal" LoRAs
- Many are compatible with both SD 1.5 and SDXL

### Installation

Download models from:
- **Civitai**: https://civitai.com/ (community models, LoRAs)
- **HuggingFace**: https://huggingface.co/ (official Stability AI models)

InvokeAI's Model Manager can import models directly from URLs or HuggingFace repo IDs.

**Note:** The FLUX models you tried earlier (FLUX.1-Krea-dev-nf4) require different architecture and may not be fully compatible with InvokeAI's current workflow system. Stick with SD 1.5 and SDXL-based models for best results.

## Architecture

The server creates a graph-based workflow for InvokeAI that includes:
1. Model loading
2. Text prompt encoding (positive and negative)
3. Noise generation
4. Latent denoising (image generation)
5. Latent-to-image conversion
6. Image saving

This workflow is automatically managed for you - just provide the prompt and parameters!
