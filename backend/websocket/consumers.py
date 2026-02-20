"""
🌸 Digital Mehndi OS — WebSocket Consumer
Real-time emotional streaming via Django Channels
Each message flows as a living packet through the pattern.
"""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from emotional_kernel.kernel import EmotionalKernel, VADVector
from memory.models import EmotionMemory, EmotionalProfile
from asgiref.sync import sync_to_async


kernel = EmotionalKernel()


class EmotionStreamConsumer(AsyncWebsocketConsumer):
    """
    WebSocket endpoint: ws://host/ws/emotion/<user_id>/
    Bidirectional emotional packet stream.
    """

    async def connect(self):
        self.user_id   = self.scope['url_route']['kwargs'].get('user_id', 'default')
        self.group     = f"emotion_{self.user_id}"
        self.vad_state = VADVector(0.0, 0.0, 0.5)   # neutral baseline
        self.history   = []

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

        # Load existing profile baseline
        profile = await self._get_or_create_profile()
        self.vad_state = VADVector(
            profile.avg_valence,
            profile.avg_arousal,
            profile.avg_dominance,
        )

        # Send welcome packet
        await self.send(json.dumps({
            'type': 'connected',
            'user_id': self.user_id,
            'baseline_vad': {
                'valence':   self.vad_state.valence,
                'arousal':   self.vad_state.arousal,
                'dominance': self.vad_state.dominance,
            },
            'dominant_emotion': profile.dominant_emotion,
            'interaction_count': profile.interaction_count,
            'message': '🌸 The pattern recognizes you. Welcome back.',
        }))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data):
        """Handle incoming message and stream back an emotional packet."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({'type': 'error', 'message': 'Invalid JSON'}))
            return

        msg_type = data.get('type', 'message')

        if msg_type == 'message':
            await self._handle_message(data)

        elif msg_type == 'vad_override':
            # Manual VAD override from frontend sliders
            self.vad_state = VADVector(
                data.get('valence',   self.vad_state.valence),
                data.get('arousal',   self.vad_state.arousal),
                data.get('dominance', self.vad_state.dominance),
            )
            await self.send(json.dumps({
                'type': 'vad_updated',
                'vad': {
                    'valence': self.vad_state.valence,
                    'arousal': self.vad_state.arousal,
                    'dominance': self.vad_state.dominance,
                },
                'emotion_label': self.vad_state.label,
                'emotion_color': self.vad_state.color,
            }))

        elif msg_type == 'get_history':
            await self._send_history(data.get('limit', 20))

        elif msg_type == 'ping':
            await self.send(json.dumps({'type': 'pong'}))

    async def _handle_message(self, data: dict):
        text = data.get('text', '').strip()
        if not text:
            return

        use_claude = data.get('use_claude', True)

        # Send "thinking" indicator
        await self.send(json.dumps({'type': 'thinking', 'pattern': self.vad_state.pattern_hash()}))

        # Process through emotional kernel
        packet = await kernel.process_async(
            text=text,
            current_vad=self.vad_state,
            history=self.history,
            use_claude=use_claude,
        )

        # Update state
        self.vad_state = packet.vad
        self.history.append(f"{text[:50]} → {packet.vad.label}")

        # Persist to SQLite
        await self._save_memory(packet)
        await self._update_profile(packet)

        # Send full emotional packet
        await self.send(json.dumps({
            'type': 'emotion_packet',
            **packet.to_dict(),
        }))

    async def _send_history(self, limit: int):
        memories = await sync_to_async(list)(
            EmotionMemory.objects.filter(user_id=self.user_id)[:limit]
        )
        await self.send(json.dumps({
            'type': 'history',
            'memories': [m.to_dict() for m in memories],
        }))

    # ── DB helpers (sync_to_async) ────────────────────────────────────────

    @sync_to_async
    def _get_or_create_profile(self) -> EmotionalProfile:
        profile, _ = EmotionalProfile.objects.get_or_create(user_id=self.user_id)
        return profile

    @sync_to_async
    def _save_memory(self, packet) -> EmotionMemory:
        import json as _json
        return EmotionMemory.objects.create(
            user_id       = self.user_id,
            input_text    = packet.input_text,
            response_text = packet.response_text,
            valence       = packet.vad.valence,
            arousal       = packet.vad.arousal,
            dominance     = packet.vad.dominance,
            emotion_label = packet.vad.label,
            pattern_hash  = packet.pattern_hash,
            latency_ms    = packet.latency_ms,
            capsules_json = _json.dumps([c.to_dict() for c in packet.capsules]),
        )

    @sync_to_async
    def _update_profile(self, packet):
        profile, _ = EmotionalProfile.objects.get_or_create(user_id=self.user_id)
        mem = EmotionMemory(
            valence=packet.vad.valence,
            arousal=packet.vad.arousal,
            dominance=packet.vad.dominance,
            emotion_label=packet.vad.label,
        )
        profile.update_from_memory(mem)

    # ── Group broadcast (from other consumers) ────────────────────────────

    async def emotion_broadcast(self, event):
        await self.send(json.dumps(event['data']))
