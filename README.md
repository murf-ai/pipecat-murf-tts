# Pipecat Murf TTS

![Murf AI Logo](https://murf.ai/public-assets/home/Murf_Logo.png)

[![pypi](https://img.shields.io/pypi/v/pipecat-murf-tts)](https://pypi.python.org/pypi/pipecat-murf-tts)

Official [Murf AI](https://murf.ai/) Text-to-Speech integration for [Pipecat](https://github.com/pipecat-ai/pipecat) - a framework for building voice and multimodal conversational AI applications.

## Table of Contents

- [Pipecat Murf TTS](#pipecat-murf-tts)
  - [Table of Contents](#table-of-contents)
  - [Pipecat Compatibility](#pipecat-compatibility)
  - [Features](#features)
  - [Installation](#installation)
    - [Using pip](#using-pip)
    - [Using uv](#using-uv)
    - [From source](#from-source)
  - [Quick Start](#quick-start)
    - [1. Get Your Murf API Key](#1-get-your-murf-api-key)
    - [2. Basic Usage](#2-basic-usage)
    - [3. Complete Example with Pipeline](#3-complete-example-with-pipeline)
  - [Configuration](#configuration)
    - [InputParams](#inputparams)
    - [Example with Custom Configuration](#example-with-custom-configuration)
  - [Available Voices](#available-voices)
  - [Environment Variables](#environment-variables)
  - [Examples](#examples)
  - [Advanced Features](#advanced-features)
    - [Dynamic Voice Changes](#dynamic-voice-changes)
    - [Error Handling](#error-handling)
  - [Requirements](#requirements)
  - [Contributing](#contributing)
  - [License](#license)
  - [Support](#support)
  - [Acknowledgments](#acknowledgments)

---

> **Note**: This integration is maintained by Murf AI. As the official provider of the TTS service, we are committed to actively maintaining and updating this integration.

## Pipecat Compatibility

**Tested with Pipecat v0.0.87**

This integration has been tested with Pipecat version 0.0.87. For compatibility with other versions, please refer to the [Pipecat changelog](https://github.com/pipecat-ai/pipecat/blob/main/CHANGELOG.md).

## Features

- 🎙️ **High-Quality Voice Synthesis**: Leverage Murf's advanced TTS technology
- 🔄 **Real-time Streaming**: WebSocket-based streaming for low-latency audio generation
- 🎨 **Voice Customization**: Control voice style, rate, pitch, and variation
- 🌍 **Multi-Language Support**: Support for multiple languages and locales
- 🔧 **Flexible Configuration**: Comprehensive audio format and quality options
- 📊 **Metrics Support**: Built-in performance tracking and monitoring

## Installation

### Using pip

```bash
pip install pipecat-murf-tts
```

### Using uv

```bash
uv add pipecat-murf-tts
```

### From source

```bash
git clone https://github.com/murf-ai/pipecat-murf-tts.git
cd pipecat-murf-tts
pip install -e .
```

## Quick Start

### 1. Get Your Murf API Key

Sign up at [Murf AI](https://murf.ai/api/dashboard) and obtain your API key from the dashboard.

### 2. Basic Usage

```python
import asyncio
from pipecat_murf_tts import MurfTTSService

async def main():
    # Initialize the TTS service
    tts = MurfTTSService(
        api_key="your-murf-api-key",
        params=MurfTTSService.InputParams(
            voice_id="en-UK-ruby",
            style="Conversational",
            rate=0,
            pitch=0,
            sample_rate=44100,
            format="PCM",
        ),
    )

    # Use in your Pipecat pipeline
    # ... (see examples below)

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Complete Example with Pipeline

```python
import asyncio
import os
from dotenv import load_dotenv
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat_murf_tts import MurfTTSService

load_dotenv()

async def main():
    # Initialize Murf TTS
    tts = MurfTTSService(
        api_key=os.getenv("MURF_API_KEY"),
        params=MurfTTSService.InputParams(
            voice_id="en-UK-ruby",
            style="Conversational",
        ),
    )

    # Initialize LLM
    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))

    # Set up context and pipeline
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
    ]
    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    # Create pipeline
    pipeline = Pipeline([
        llm,
        tts,
        context_aggregator.assistant(),
    ])

    # Run pipeline
    task = PipelineTask(pipeline)
    runner = PipelineRunner()
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

### InputParams

The `MurfTTSService.InputParams` class provides extensive configuration options:

| Parameter | Type | Default | Range/Options | Description |
|-----------|------|---------|---------------|-------------|
| `voice_id` | `str` | `"en-UK-ruby"` | Any valid Murf voice ID | Voice identifier for TTS synthesis |
| `style` | `str` | `"Conversational"` | Voice-specific styles | Voice style (e.g., "Conversational", "Narration") |
| `rate` | `int` | `0` | `-50` to `50` | Speech rate adjustment |
| `pitch` | `int` | `0` | `-50` to `50` | Pitch adjustment |
| `variation` | `int` | `1` | `0` to `5` | Variation in pause, pitch, and speed (Gen2 only) |
| `model` | `str` | `"FALCON"` | `"FALCON"`, `"GEN2"` | The model to use for audio output |
| `sample_rate` | `int` | `44100` | `8000`, `24000`, `44100`, `48000` | Audio sample rate in Hz |
| `channel_type` | `str` | `"MONO"` | `"MONO"`, `"STEREO"` | Audio channel configuration |
| `format` | `str` | `"PCM"` | `"MP3"`, `"WAV"`, `"FLAC"`, `"ALAW"`, `"ULAW"`, `"PCM"`, `"OGG"` | Audio output format |
| `multi_native_locale` | `str` | `None` | Language codes (e.g., `"en-US"`) | Language for Gen2 model audio |
| `pronunciation_dictionary` | `dict` | `None` | Custom pronunciation mappings | Dictionary for custom word pronunciations |

### Example with Custom Configuration

```python
from pipecat_murf_tts import MurfTTSService

tts = MurfTTSService(
    api_key="your-api-key",
    params=MurfTTSService.InputParams(
        voice_id="en-US-natalie",
        style="Narration",
        rate=10,  # Slightly faster
        pitch=-5,  # Slightly lower pitch
        variation=3,  # More variation
        sample_rate=48000,  # Higher quality
        channel_type="STEREO",
        format="WAV",
        multi_native_locale="en-US",
        pronunciation_dictionary={
            "Pipecat": {"pronunciation": "pipe-cat"},
        },
    ),
)
```

## Available Voices

Murf AI offers a wide variety of voices across different languages and styles. Visit the [Murf AI Voice Library](https://murf.ai/api/dashboard) to explore available voices.

Common voice IDs include:
- `en-US-natalie` - American English, female
- `en-UK-ruby` - British English, female
- `en-US-amara` - American English, female
- And many more...

## Environment Variables

Create a `.env` file in your project root:

```env
MURF_API_KEY=your_murf_api_key_here
OPENAI_API_KEY=your_openai_key_here  # If using with LLM
DEEPGRAM_API_KEY=your_deepgram_key_here  # If using with STT
```

## Examples

Check out the [examples](./examples) directory for complete working examples:

- **[murf_tts_basic.py](./examples/foundational/murf_tts_basic.py)** - Full pipeline with STT, LLM, and TTS

To run the example:

```bash
# Install example dependencies
uv add pipecat-ai[deepgram,openai,silero]

# Set up your .env file with API keys
# Then run
python examples/foundational/murf_tts_basic.py
```

## Advanced Features

### Dynamic Voice Changes

```python
# Change voice on the fly
tts.set_voice("en-US-natalie")
```

### Error Handling

The service includes built-in error handling and automatic reconnection:

```python
tts = MurfTTSService(
    api_key="your-api-key",
    params=MurfTTSService.InputParams(voice_id="en-UK-ruby"),
)

# Automatic reconnection on connection loss
# Built-in context management for interruptions
```

## Requirements

- Python >= 3.10, < 3.13
- pipecat-ai >= 0.0.87, < 0.1.0
- websockets >= 15.0.1, < 16.0
- loguru >= 0.7.3
- python-dotenv >= 1.1.1

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: support@murf.ai
- 🌐 Website: [murf.ai](https://murf.ai/)
- 📖 Documentation: [Murf API Documentation](https://murf.ai/api/docs)
- 🐛 Issues: [GitHub Issues](https://github.com/murf-ai/pipecat-murf-tts/issues)

## Acknowledgments

- Built for [Pipecat](https://github.com/pipecat-ai/pipecat) by Daily
- Powered by [Murf AI](https://murf.ai/) TTS technology
