# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **VAE Override Support**: Added ability to override model's built-in VAE with external VAE models
  - New `vae_key` parameter in both `generate_image` and `img2img` tools
  - Automatic VAE loader node insertion when `vae_key` is specified
  - Supports fixing models with corrupt/missing VAEs (e.g., sd_xl_base_1.0)
  - Enables optimization with specialized VAEs (e.g., sdxl-vae-fp16-fix for FP16 compatibility)
  - VAE routing dynamically switches between `vae_loader` and `model_loader` based on override
- **LoRA Support**: Added support for LoRA (Low-Rank Adaptation) models in both text-to-image and image-to-image generation
  - New `lora_key` parameter to specify LoRA model identifier
  - New `lora_weight` parameter (0.0-2.0) to control LoRA strength
  - Automatic LoRA loader node insertion in graph workflows
  - Updated README with LoRA usage examples and workflow
  - Tested with logomkrdsxl LoRA for logo generation
- **Full SDXL Support**: Automatic SDXL model detection and proper graph construction
  - Automatic detection of SDXL models based on `model_info["base"] == "sdxl"`
  - Use `sdxl_model_loader` node type for SDXL models instead of `main_model_loader`
  - Use `sdxl_compel_prompt` node type for SDXL prompts with style field support
  - Dual CLIP encoder support (clip and clip2) for SDXL models
  - Proper clip2 routing: directly from model_loader (bypasses LoRA loader which doesn't support clip2)

### Changed
- Refactored graph building in `create_text2img_graph()` to use dynamic node/edge construction
- Refactored graph building in `create_img2img_graph()` to use dynamic node/edge construction
- Updated tool schemas for `generate_image` and `img2img` to include LoRA and VAE parameters
- VAE routing now uses `vae_source` variable for flexible source selection

### Fixed
- **Black Images with SDXL Models**: Resolved black image output from models with corrupt/missing VAEs
  - Root cause: sd_xl_base_1.0 and similar models have corrupt or incompatible built-in VAEs
  - Solution: Implemented VAE override feature to use external VAE models (sdxl.vae, sdxl-vae-fp16-fix)
  - Verified with successful test generation (1.6MB proper image vs 17-20KB black images)
- **SDXL Model Compatibility**: Fixed SDXL models failing with `main_model_loader` and `compel` nodes
- **SDXL + LoRA clip2 Routing**: Fixed incorrect attempt to route clip2 through lora_loader
  - Root cause: lora_loader node doesn't have clip2 input/output fields in InvokeAI architecture
  - Solution: Route clip2 directly from model_loader to prompt nodes, bypassing lora_loader
  - UNet and clip still route through lora_loader for proper LoRA application
- **Early Failure Detection**: Added immediate error detection in `wait_for_completion()` to prevent timeout waits
- **Model Info Validation**: Added isinstance() type checking before validation to prevent TypeError
- **Error Handling**: Improved exception handling in `get_model_info()` with proper logging

## [1.0.0] - 2025-01-XX

### Added
- Initial release of InvokeAI MCP Server
- Text-to-image generation via `generate_image` tool
- Image-to-image transformation via `img2img` tool
- AI-powered upscaling via `upscale_image` tool
- Model listing via `list_models` tool
- Queue status monitoring via `get_queue_status` tool
- Support for Stable Diffusion 1.5 and SDXL models
- Comprehensive parameter control (width, height, steps, CFG scale, schedulers, seeds)
- Graph-based workflow system
- MIT License
