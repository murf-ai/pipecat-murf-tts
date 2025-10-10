# Pipecat Murf TTS

![Murf AI Logo](https://murf.ai/public-assets/home/Murf_Logo.png)

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration Options](#configuration-options)
- [Contributing](#contributing)

---

## Overview

The **Pipecat Murf TTS** integration provides seamless text-to-speech capabilities for [Pipecat](https://github.com/pipecat-ai/pipecat) applications using Murf AI's powerful voice synthesis technology. With over 130 natural-sounding voices across 13+ languages and 20+ speaking styles, this integration enables developers to build rich, multimodal conversational AI applications with high-quality voice output.

Pipecat is a framework for building voice and multimodal AI applications, and this integration brings Murf's industry-leading TTS capabilities directly into your Pipecat pipelines.

### Key Features

- **Real-time streaming TTS** via WebSocket API
- **130+ natural voices** across multiple languages and accents
- **20+ speaking styles** for different contexts and emotions
- **Extensive voice customization**: rate, pitch, variation, and pronunciation dictionaries
- **Flexible audio output**: Multiple sample rates (8kHz - 48kHz) and formats (PCM, MP3, WAV, FLAC, OGG)
- **Seamless Pipecat integration**: Works with other Pipecat services (LLM, STT, etc.)

---

## Installation

### Prerequisites

- Python 3.10, 3.11, or 3.12
- A Murf API key from [Murf API Dashboard](https://murf.ai/api/dashboard)

### Using uv (Recommended)

1. **Install `uv`** (Python package manager) - See [official uv installation guide](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)

2. **Install the package:**
   ```bash
   uv pip install pipecat-murf-tts
   ```

### Using pip

```bash
pip install pipecat-murf-tts
```

### From Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/murf-ai/pipecat-murf-tts.git
   cd pipecat-murf-tts
   ```

2. **Install dependencies:**
   ```bash
   uv pip install -e .
   ```
   
   Or with pip:
   ```bash
   pip install -e .
   ```

---

## Usage

### Basic Setup

Here's a minimal example of how to use Murf TTS in your Pipecat pipeline:

```python
import os
from pipecat_murf_tts.tts import MurfTTSService

# Initialize the Murf TTS service
tts = MurfTTSService(
    api_key=os.getenv("MURF_API_KEY"),
    params=MurfTTSService.InputParams(
        voice_id="en-UK-ruby",
        style="Conversational",
        rate=0,
        pitch=0,
    ),
)

# Add to your Pipecat pipeline
pipeline = Pipeline([
    # ... other components
    tts,
    # ... other components
])
```

### Complete Voice Bot Example

For a complete working example that combines STT (Deepgram), LLM (OpenAI), and TTS (Murf), see `examples/foundational/murf_tts_basic.py`:

```bash
# Set up your environment variables
export MURF_API_KEY="your-murf-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export DEEPGRAM_API_KEY="your-deepgram-api-key"

# Run the example
python examples/foundational/murf_tts_basic.py
```

This example creates a fully interactive voice bot that:
1. Listens to your speech (Deepgram STT)
2. Processes it with an LLM (OpenAI)
3. Responds with natural voice (Murf TTS)

---

## Configuration Options

The `MurfTTSService.InputParams` class provides extensive customization options:

### Voice Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `voice_id` | `str` | `"en-UK-ruby"` | Voice ID to use for TTS. Browse available voices in the [Murf API Dashboard](https://murf.ai/api/dashboard) |
| `style` | `str` | `"Conversational"` | Speaking style (e.g., "Conversational", "Narrative", "Promotional") |

### Voice Modulation

| Parameter | Type | Range | Default | Description |
|-----------|------|-------|---------|-------------|
| `rate` | `int` | -50 to 50 | 0 | Speed of the voiceover (negative = slower, positive = faster) |
| `pitch` | `int` | -50 to 50 | 0 | Pitch of the voice (negative = lower, positive = higher) |
| `variation` | `int` | 0 to 5 | 1 | Variation in pause, pitch, and speed (Gen2 model only) |

### Audio Output

| Parameter | Type | Options | Default | Description |
|-----------|------|---------|---------|-------------|
| `sample_rate` | `int` | 8000, 24000, 44100, 48000 | 44100 | Sample rate for audio output |
| `channel_type` | `str` | MONO, STEREO | "MONO" | Audio channel type |
| `format` | `str` | PCM, MP3, WAV, FLAC, ALAW, ULAW, OGG | "PCM" | Audio format |

### Advanced Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pronunciation_dictionary` | `Dict[str, Dict[str, str]]` | `None` | Custom pronunciation mappings for specific words |
| `multi_native_locale` | `str` | `None` | Language locale for Gen2 model (e.g., "en-US", "en-UK") |

### Example with Custom Configuration

```python
tts = MurfTTSService(
    api_key=os.getenv("MURF_API_KEY"),
    params=MurfTTSService.InputParams(
        voice_id="en-US-natalie",
        style="Narrative",
        rate=10,  # Slightly faster
        pitch=-5,  # Slightly lower pitch
        variation=3,  # More variation
        sample_rate=48000,  # High quality
        pronunciation_dictionary={
            "API": {"pronunciation": "ay pee eye"},
            "Pipecat": {"pronunciation": "pipe cat"}
        }
    ),
)
```

---

## Contributing

Contributions are welcome! If you'd like to improve the Pipecat Murf TTS integration, follow these steps:

1. **Fork the repository** and clone it to your machine:
   ```bash
   git clone https://github.com/murf-ai/pipecat-murf-tts.git
   cd pipecat-murf-tts
   ```

2. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Install development dependencies**:
   ```bash
   uv pip install -e ".[dev]"
   ```

4. **Make your changes** and ensure everything runs smoothly:
   ```bash
   # Run tests
   pytest
   
   # Run linter
   ruff check .
   
   # Run type checker
   mypy src/
   ```

5. **Write clear commit messages** and keep the code clean.

6. **Open a pull request** describing your changes.

Feel free to open an issue if you have questions, feature requests, or need help getting started.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Resources

- [Murf AI Platform](https://murf.ai/)
- [Murf API Documentation](https://murf.ai/api/docs)
- [Murf API Dashboard](https://murf.ai/api/dashboard)
- [Pipecat Framework](https://github.com/pipecat-ai/pipecat)
- [GitHub Repository](https://github.com/murf-ai/pipecat-murf-tts)
