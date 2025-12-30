# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2025-12-30

### Fixed
- Fixed bug where `end:true` was sent on all TTS chunks. Now `end:true` is only sent once via `flush_audio` after all LLM-generated chunks are sent to TTS to properly mark the end of the turn

### Changed
- Removed redundant `audio_context_available` checks before calling `remove_audio_context` (parent class handles this internally)
- Code cleanup and improvements

## [0.1.2] - 2025-12-17

### Added
- Added `aggregated_by="sentence"` parameter to `TTSTextFrame` for proper text frame aggregation

### Changed
- Updated error handling to use `push_error` method instead of `ErrorFrame`
- Updated pipecat dependency to 0.0.97 in pyproject.toml and uv.lock

## [0.1.1] - 2025-12-04

### Fixed
- Added 16000 Hz as a valid sample rate option (previously only 8000, 24000, 44100, 48000 were supported)

## [0.1.0] - 2025-11-07

### Added
- Initial release of Murf TTS integration for Pipecat
- WebSocket-based streaming TTS service implementation
- Support for voice customization (style, rate, pitch, variation)
- Multi-language and locale support
- Audio format options (PCM, WAV, MP3, FLAC, etc.)
- Sample rate configuration (8000, 16000, 24000, 44100, 48000 Hz)
- Channel type support (MONO, STEREO)
- Pronunciation dictionary support
- Metrics and monitoring support
- Error handling with automatic reconnection
- Interruption handling with context management
