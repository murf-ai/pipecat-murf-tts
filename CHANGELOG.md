# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] - 2026-07-14

### Changed
- **Expanded pipecat-ai compatibility** to support versions `>=0.0.108,<2.0.0` (previously capped at `<=0.1.0`).

## [0.2.1] - 2026-05-14

### Changed
- **Minimum pipecat-ai version raised to 0.0.108** (from 0.0.106).
- **Minimum Python version raised to 3.11** (from 3.10); removed upper bound (`<3.13`).

## [0.2.0] - 2026-03-21

### Breaking Changes
- **Minimum pipecat-ai version raised to 0.0.106** (from 0.0.97).
- **`aggregate_sentences` parameter removed** from `__init__`. Use `text_aggregation_mode` (`TextAggregationMode.SENTENCE` or `TextAggregationMode.TOKEN`) instead.
- **`set_voice()` is no longer overridden**. The parent's deprecated `set_voice()` (async) is now used, which routes through `TTSUpdateSettingsFrame`. Callers using the old synchronous `set_voice(voice_id)` must switch to `await set_voice(voice_id)` or use `TTSUpdateSettingsFrame(voice=...)`.
- **`_handle_interruption()` replaced by `on_audio_context_interrupted()`** to match the new pipecat audio context lifecycle.
- **`run_tts()` signature changed**: now requires a `context_id` parameter (`run_tts(text, context_id)` instead of `run_tts(text)`).
- **`flush_audio()` signature changed**: now accepts an optional `context_id` parameter.

### Changed
- Voice is now stored in the standard `TTSSettings.voice` field and read from `self._settings.voice`, enabling runtime voice changes via `TTSUpdateSettingsFrame(voice=...)`.
- Removed `_update_settings()` override, the parent class handles settings updates.
- Context management now delegated to the parent's audio context system (`create_audio_context`, `remove_audio_context`, `remove_active_audio_context`, `reset_active_audio_context`) instead of manual `self._context_id` tracking.

### Changed (Example)
- Updated `murf_tts_basic.py` to use the new pipecat 0.0.106 APIs: `LLMContext`, `LLMContextAggregatorPair`, `LLMUserAggregatorParams`, `LLMMessagesAppendFrame`, and `LLMRunFrame`.
- VAD analyzer moved from `LocalAudioTransportParams` to `LLMUserAggregatorParams`.

## [0.1.4] - 2025-12-31

### Changed
- Synced uv.lock with version 0.1.4

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
