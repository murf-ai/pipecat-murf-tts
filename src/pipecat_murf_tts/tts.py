"""Murf AI text-to-speech service implementation."""

import asyncio
import base64
import json
from typing import AsyncGenerator, Dict, Optional, Any, Literal, Union

from loguru import logger
from pydantic import BaseModel, field_validator

from pipecat.frames.frames import (
    CancelFrame,
    EndFrame,
    ErrorFrame,
    Frame,
    StartFrame,
    TTSAudioRawFrame,
    TTSStoppedFrame,
)
from pipecat.services.settings import TTSSettings
from pipecat.services.tts_service import TextAggregationMode, WebsocketTTSService
from pipecat.utils.tracing.service_decorators import traced_tts

# See .env.example for Murf configuration needed
try:
    from websockets.asyncio.client import ClientConnection, connect as websocket_connect
    from websockets.protocol import State
except ModuleNotFoundError as e:
    logger.error(f"Exception: {e}")
    raise Exception(f"Missing module: {e}")


class MurfTTSService(WebsocketTTSService):
    """Murf AI WebSocket-based text-to-speech service.

    Provides real-time text-to-speech synthesis using Murf's WebSocket API.
    Supports various voice customization options including style, rate, pitch,
    and pronunciation dictionaries.
    """

    class InputParams(BaseModel):
        """Input parameters for Murf TTS configuration.

        Parameters:
            voice_id: Voice ID to use for TTS. Defaults to "Matthew".
            style: The voice style to be used for voiceover generation.
            rate: Speed of the voiceover. Range: -50 to 50.
            pitch: Pitch of the voiceover. Range: -50 to 50.
            pronunciation_dictionary: A map of words to their pronunciation details.
            variation: Higher values add more variation in Pause, Pitch, and Speed. Range: 0-5.
                      Only available for Gen2 model. Defaults to 1.
            multi_native_locale: Language for generated audio in Gen2 model (e.g., "en-US", "en-UK").
            model: The model to use for audio output. Defaults to "FALCON".
                      Currently supports "FALCON" and "GEN2".
            sample_rate: The sample rate for audio output. Valid values: 8000, 16000, 24000, 44100, 48000.
                        Defaults to 44100.
            channel_type: The channel type for audio output. Valid values: MONO, STEREO. Defaults to "MONO".
            format: The audio format for output. Valid values: MP3, WAV, FLAC, ALAW, ULAW, PCM, OGG.
                   Defaults to "PCM".
        """

        voice_id: Optional[str] = "Matthew"
        style: Optional[str] = "Conversational"
        rate: Optional[int] = 0
        pitch: Optional[int] = 0
        pronunciation_dictionary: Optional[Dict[str, Dict[str, str]]] = None
        variation: Optional[int] = 1
        multi_native_locale: Optional[str] = None
        model: Optional[Union[Literal["FALCON", "GEN2"], str]] = "FALCON"
        sample_rate: Optional[int] = 44100
        channel_type: Optional[str] = "MONO"
        format: Optional[str] = "PCM"

        @field_validator("voice_id")
        @classmethod
        def validate_voice_id(cls, v: Optional[str]) -> Optional[str]:
            if v is not None and not v.strip():
                raise ValueError("voice_id cannot be empty or whitespace")
            return v

        @field_validator("sample_rate")
        @classmethod
        def validate_sample_rate(cls, v: Optional[int]) -> Optional[int]:
            valid_rates = [8000, 16000, 24000, 44100, 48000]
            if v is not None and v not in valid_rates:
                raise ValueError(f"sample_rate must be one of {valid_rates}, got {v}")
            return v

        @field_validator("rate")
        @classmethod
        def validate_rate(cls, v: Optional[int]) -> Optional[int]:
            if v is not None and not (-50 <= v <= 50):
                raise ValueError(f"rate must be between -50 and 50, got {v}")
            return v

        @field_validator("pitch")
        @classmethod
        def validate_pitch(cls, v: Optional[int]) -> Optional[int]:
            if v is not None and not (-50 <= v <= 50):
                raise ValueError(f"pitch must be between -50 and 50, got {v}")
            return v

        @field_validator("variation")
        @classmethod
        def validate_variation(cls, v: Optional[int]) -> Optional[int]:
            if v is not None and not (0 <= v <= 5):
                raise ValueError(f"variation must be between 0 and 5, got {v}")
            return v

        @field_validator("channel_type")
        @classmethod
        def validate_channel_type(cls, v: Optional[str]) -> Optional[str]:
            valid_types = ["MONO", "STEREO"]
            if v is not None and v not in valid_types:
                raise ValueError(f"channel_type must be one of {valid_types}, got {v}")
            return v

        @field_validator("format")
        @classmethod
        def validate_format(cls, v: Optional[str]) -> Optional[str]:
            valid_formats = ["MP3", "WAV", "FLAC", "ALAW", "ULAW", "PCM", "OGG"]
            if v is not None and v not in valid_formats:
                raise ValueError(f"format must be one of {valid_formats}, got {v}")
            return v

    def __init__(
        self,
        *,
        api_key: str,
        url: str = "wss://global.api.murf.ai/v1/speech/stream-input",
        params: Optional[InputParams] = None,
        text_aggregation_mode: Optional[TextAggregationMode] = None,
        **kwargs,
    ):
        """Initialize the Murf TTS service.

        Args:
            api_key: Murf API key for authentication.
            url: WebSocket URL for Murf TTS API.
            params: Additional input parameters for voice customization.
            text_aggregation_mode: How to aggregate incoming text before synthesis.
            **kwargs: Additional arguments passed to parent WebsocketTTSService.

        Raises:
            ValueError: If api_key is empty or contains only whitespace.
        """
        params = params or MurfTTSService.InputParams()

        default_settings = TTSSettings(
            model=None,
            voice=params.voice_id or "Matthew",
            language=None,
        )

        super().__init__(
            text_aggregation_mode=text_aggregation_mode,
            push_text_frames=True,
            push_start_frame=True,
            pause_frame_processing=False,
            settings=default_settings,
            **kwargs,
        )

        if not api_key or not api_key.strip():
            raise ValueError("Murf API key is required and cannot be empty")

        self._api_key = api_key
        self._url = url
        self._murf_settings = {
            "style": params.style,
            "rate": params.rate,
            "pitch": params.pitch,
            "pronunciation_dictionary": params.pronunciation_dictionary or {},
            "variation": params.variation,
            "multi_native_locale": params.multi_native_locale,
            "model": params.model,
            "sample_rate": params.sample_rate,
            "channel_type": params.channel_type,
            "format": params.format,
        }

        self._receive_task: Optional[asyncio.Task[None]] = None
        self._websocket: Optional[ClientConnection] = None

    def can_generate_metrics(self) -> bool:
        """Check if this service can generate processing metrics.

        Returns:
            True, as Murf service supports metrics generation.
        """
        return True

    async def _verify_connection(self) -> bool:
        """Verify the websocket connection is active and responsive.

        Returns:
            True if connection is verified working, False otherwise.
        """
        try:
            if not self._websocket:
                return False
            await self._websocket.ping()
            return True
        except Exception as e:
            logger.error(f"{self} connection verification failed: {e}")
            return False

    async def start(self, frame: StartFrame) -> None:
        """Start the Murf TTS service.

        Args:
            frame: The start frame containing initialization parameters.
        """
        await super().start(frame)
        self._murf_settings["sample_rate"] = self.sample_rate
        await self._connect()

    async def stop(self, frame: EndFrame) -> None:
        """Stop the Murf TTS service.

        Args:
            frame: The end frame.
        """
        await super().stop(frame)
        await self._disconnect()

    async def cancel(self, frame: CancelFrame) -> None:
        """Cancel the Murf TTS service.

        Args:
            frame: The cancel frame.
        """
        await super().cancel(frame)
        await self._disconnect()

    async def _connect(self):
        """Connect to Murf WebSocket and start receive task."""
        await super()._connect()

        await self._connect_websocket()

        if self._websocket and not self._receive_task:
            self._receive_task = self.create_task(
                self._receive_task_handler(self._report_error)
            )

    async def _disconnect(self) -> None:
        """Disconnect from Murf WebSocket and clean up tasks."""
        await super()._disconnect()

        if self._receive_task:
            await self.cancel_task(self._receive_task)
            self._receive_task = None

        await self._disconnect_websocket()

    async def _connect_websocket(self) -> None:
        """Connect to Murf websocket."""
        try:
            if self._websocket and self._websocket.state is State.OPEN:
                return

            url = (
                f"{self._url}"
                f"?sample_rate={self._murf_settings['sample_rate']}"
                f"&format={self._murf_settings['format']}"
                f"&channel_type={self._murf_settings['channel_type']}"
                f"&model={self._murf_settings['model']}"
            )

            headers = {"api-key": self._api_key}

            logger.debug("Connecting to Murf")
            self._websocket = await websocket_connect(url, additional_headers=headers)
            logger.debug("Connected to Murf")

        except Exception as e:
            logger.error(f"{self} initialization error: {e}")
            self._websocket = None
            await self.push_error(
                error_msg=f"{self} connection error: {e}", exception=e
            )

    async def _disconnect_websocket(self) -> None:
        """Disconnect from Murf websocket."""
        try:
            await self.stop_all_metrics()

            if self._websocket:
                logger.debug("Disconnecting from Murf")
                await self._websocket.close()
        except Exception as e:
            logger.error(f"{self} error closing websocket: {e}")
        finally:
            await self.remove_active_audio_context()
            self._websocket = None

    def _get_websocket(self) -> ClientConnection:
        """Get the WebSocket connection if available.

        Returns:
            The active websocket connection.

        Raises:
            Exception: If websocket is not connected.
        """
        if self._websocket:
            return self._websocket
        raise Exception("Websocket not connected")

    async def flush_audio(self, context_id: Optional[str] = None):
        """Flush any pending audio and finalize the current turn.

        Args:
            context_id: The specific context to flush. If None, falls back to the
                currently active context.
        """
        flush_id = context_id or self.get_active_audio_context_id()
        if not flush_id or not self._websocket:
            return

        logger.debug(f"{self}: flushing audio and finalizing turn")
        try:
            end_msg = {"context_id": flush_id, "end": True}
            end_msg_json = json.dumps(end_msg)
            await self._websocket.send(end_msg_json)
            logger.debug(f"{self} marked turn complete for context {flush_id}")
        except Exception as e:
            logger.error(f"{self} error flushing audio: {e}")

    async def on_audio_context_interrupted(self, context_id: str):
        """Cancel the active Murf context when the bot is interrupted.

        Args:
            context_id: The ID of the audio context that was interrupted.
        """
        await self.stop_all_metrics()
        if context_id and self._websocket:
            try:
                clear_msg = json.dumps({"clear": True, "context_id": context_id})
                await self._websocket.send(clear_msg)
                logger.debug(f"{self} cleared context {context_id}")
            except Exception as e:
                logger.error(f"{self} error cancelling context: {e}")

    async def _process_messages(self) -> None:
        """Process messages from Murf WebSocket."""
        async for message in self._get_websocket():
            try:
                if isinstance(message, str):
                    data = json.loads(message)
                    await self._process_json_message(data)
                else:
                    logger.warning(
                        f"{self} received unexpected non-string message: {type(message)}"
                    )
            except Exception as e:
                logger.error(f"{self} error processing message: {e}")
                await self.push_error(
                    error_msg=f"{self} error processing message: {e}", exception=e
                )

    async def _receive_messages(self) -> None:
        """Receive and process messages from Murf WebSocket."""
        while True:
            await self._process_messages()
            # Connection closed/timed out, reconnect
            logger.debug(f"{self} websocket connection ended, reconnecting")
            await self._connect_websocket()

    async def _process_json_message(self, data: Dict[str, Any]) -> None:
        """Process JSON messages from Murf.

        Handles two message types:
        1. audioOutput: Contains base64-encoded audio data
        2. finalOutput: Indicates end of synthesis (final=true)

        Args:
            data: JSON message data from Murf websocket.
        """
        received_ctx_id = data.get("context_id")

        if not received_ctx_id or not isinstance(received_ctx_id, str):
            logger.warning(f"Missing or invalid context_id in message: {data}")
            return

        if not self.audio_context_available(received_ctx_id):
            return

        if "error" in data:
            error_msg = f"{self} error: {data['error']}"
            logger.error(error_msg)
            await self.push_frame(TTSStoppedFrame(context_id=received_ctx_id))
            await self.stop_all_metrics()
            await self.push_error(error_msg=error_msg)
            self.reset_active_audio_context()
            return

        if "audio" in data:
            try:
                audio_b64 = data["audio"]
                audio_data = base64.b64decode(audio_b64)
                await self._process_audio_data_to_context(received_ctx_id, audio_data)
            except Exception as e:
                logger.error(f"{self} error decoding audio data: {e}")
            return

        if data.get("final") is True:
            logger.debug(f"{self} received final output for context {received_ctx_id}")
            await self.stop_ttfb_metrics()
            await self.remove_audio_context(received_ctx_id)
            return

        logger.debug(f"{self} received unknown message: {data}")

    async def _process_audio_data_to_context(
        self, context_id: str, audio_data: bytes
    ) -> None:
        """Process decoded audio data from Murf and append to context.

        Args:
            context_id: The audio context identifier.
            audio_data: Raw PCM audio data bytes.
        """
        frame = TTSAudioRawFrame(
            audio=audio_data,
            sample_rate=self.sample_rate,
            num_channels=1,
            context_id=context_id,
        )
        await self.append_to_audio_context(context_id, frame)

    def _build_voice_config_message(
        self, text: str, context_id: str, is_last: bool = False
    ) -> Dict[str, Any]:
        """Build voice configuration message for Murf API.

        Args:
            text: The text to synthesize.
            context_id: The context ID for this synthesis request.
            is_last: Whether this is the last message in the sequence.
        """
        voice_config: Dict[str, Any] = {
            "voice_id": self._settings.voice,
            "style": self._murf_settings["style"],
            "rate": self._murf_settings["rate"],
            "pitch": self._murf_settings["pitch"],
            "pronunciation_dictionary": self._murf_settings["pronunciation_dictionary"],
            "variation": self._murf_settings["variation"],
        }

        if self._murf_settings["multi_native_locale"]:
            voice_config["multi_native_locale"] = self._murf_settings[
                "multi_native_locale"
            ]

        message: Dict[str, Any] = {
            "voice_config": voice_config,
            "context_id": context_id,
            "text": text,
            "end": is_last,
        }
        logger.debug(f"{self} voice config message: {message}")

        return message

    @traced_tts
    async def run_tts(self, text: str, context_id: str) -> AsyncGenerator[Frame, None]:
        """Generate speech from text using Murf's streaming WebSocket API.

        Args:
            text: The text to synthesize into speech.
            context_id: The context ID for tracking audio frames.

        Yields:
            Frame: Audio frames containing the synthesized speech.
        """
        logger.debug(f"{self}: Generating TTS [{text}]")

        try:
            if not self._websocket or self._websocket.state is State.CLOSED:
                await self._connect()

            voice_config_msg = self._build_voice_config_message(
                text, context_id=context_id, is_last=False
            )

            try:
                voice_config_json = json.dumps(voice_config_msg)
                await self._get_websocket().send(voice_config_json)
                await self.start_tts_usage_metrics(text)
            except Exception as e:
                yield ErrorFrame(error=f"Error sending message: {e}")
                yield TTSStoppedFrame(context_id=context_id)
                await self._disconnect()
                await self._connect()
                return

            return
        except Exception as e:
            yield ErrorFrame(error=f"Unknown error occurred: {e}")


__all__ = ["MurfTTSService"]
