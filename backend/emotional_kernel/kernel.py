"""
🌸 Digital Mehndi OS — Emotional Kernel
The zero-payload VAD processing core.
Valence · Arousal · Dominance → Emotion Capsules → Pattern
"""
import math
import time
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Optional
import anthropic
from django.conf import settings


# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VADVector:
    """Valence-Arousal-Dominance emotion representation."""
    valence: float    # -1.0 (sad/negative) → +1.0 (happy/positive)
    arousal: float    # -1.0 (calm/still)   → +1.0 (excited/intense)
    dominance: float  # -1.0 (fearful/weak) → +1.0 (powerful/dominant)

    def __post_init__(self):
        self.valence   = max(-1.0, min(1.0, self.valence))
        self.arousal   = max(-1.0, min(1.0, self.arousal))
        self.dominance = max(-1.0, min(1.0, self.dominance))

    def to_list(self) -> List[float]:
        return [self.valence, self.arousal, self.dominance]

    def distance_to(self, other: 'VADVector') -> float:
        return math.sqrt(
            (self.valence   - other.valence)   ** 2 +
            (self.arousal   - other.arousal)   ** 2 +
            (self.dominance - other.dominance) ** 2
        )

    def blend_with(self, other: 'VADVector', weight: float) -> 'VADVector':
        w = max(0.0, min(1.0, weight))
        return VADVector(
            self.valence   * (1 - w) + other.valence   * w,
            self.arousal   * (1 - w) + other.arousal   * w,
            self.dominance * (1 - w) + other.dominance * w,
        )

    def pattern_hash(self) -> str:
        raw = f"{self.valence:.2f}{self.arousal:.2f}{self.dominance:.2f}"
        return f"knot-{hashlib.md5(raw.encode()).hexdigest()[:8]}"

    @property
    def label(self) -> str:
        if self.valence > 0.5 and self.arousal > 0.3:   return "Joy"
        if self.valence > 0.5 and self.arousal < -0.2:  return "Peace"
        if self.valence < -0.4 and self.arousal > 0.4:  return "Anger"
        if self.valence < -0.4 and self.arousal < 0.0:  return "Sorrow"
        if self.arousal > 0.6:                           return "Awe"
        if abs(self.valence) < 0.2 and abs(self.arousal) < 0.2: return "Calm"
        return "Neutral"

    @property
    def color(self) -> str:
        r = int(139 + self.valence * 60)
        g = int(69  + self.arousal * 50)
        b = int(19  + self.dominance * 30)
        return f"rgb({min(255,max(0,r))},{min(255,max(0,g))},{min(255,max(0,b))})"


@dataclass
class EmotionCapsule:
    """A named emotion capsule with VAD coordinates and weight."""
    cid: str
    name: str
    vad: VADVector
    weight: float = 1.0
    layer: str = "base"        # base | overlay | context
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'cid': self.cid,
            'name': self.name,
            'vad': asdict(self.vad),
            'weight': self.weight,
            'layer': self.layer,
            'tags': self.tags,
        }


@dataclass
class EmotionalPacket:
    """A complete emotional packet ready for WebSocket delivery."""
    timestamp: float
    input_text: str
    vad: VADVector
    capsules: List[EmotionCapsule]
    pattern_hash: str
    latency_ms: float
    mandala_petals: int
    vine_curve: float
    response_text: str = ""

    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp,
            'input_text': self.input_text,
            'vad': asdict(self.vad),
            'capsules': [c.to_dict() for c in self.capsules],
            'pattern_hash': self.pattern_hash,
            'latency_ms': self.latency_ms,
            'mandala_petals': self.mandala_petals,
            'vine_curve': self.vine_curve,
            'emotion_label': self.vad.label,
            'emotion_color': self.vad.color,
            'response_text': self.response_text,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Capsule Library  (built-in emotion atlas)
# ─────────────────────────────────────────────────────────────────────────────

CAPSULE_ATLAS: List[EmotionCapsule] = [
    EmotionCapsule("joy",     "Joy",      VADVector( 0.8,  0.6,  0.5), tags=["positive","high"]),
    EmotionCapsule("peace",   "Peace",    VADVector( 0.7,  0.1,  0.6), tags=["positive","low"]),
    EmotionCapsule("awe",     "Awe",      VADVector( 0.4,  0.8,  0.2), tags=["high","neutral"]),
    EmotionCapsule("calm",    "Calm",     VADVector( 0.1,  0.0,  0.4), tags=["low","neutral"]),
    EmotionCapsule("sorrow",  "Sorrow",   VADVector(-0.7,  0.2, -0.3), tags=["negative","low"]),
    EmotionCapsule("anger",   "Anger",    VADVector(-0.6,  0.8,  0.4), tags=["negative","high"]),
    EmotionCapsule("fear",    "Fear",     VADVector(-0.8,  0.7, -0.7), tags=["negative","high"]),
    EmotionCapsule("desire",  "Desire",   VADVector( 0.6,  0.7,  0.5), tags=["positive","high"]),
    EmotionCapsule("wonder",  "Wonder",   VADVector( 0.5,  0.6,  0.1), tags=["positive","high"]),
    EmotionCapsule("resolve", "Resolve",  VADVector( 0.3,  0.4,  0.9), tags=["neutral","high"]),
]


# ─────────────────────────────────────────────────────────────────────────────
# Kernel
# ─────────────────────────────────────────────────────────────────────────────

class EmotionalKernel:
    """
    Zero-payload emotional processing core.
    Input: raw text → Output: EmotionalPacket (target < 50ms local)
    """

    # Simple lexicon for fast local inference (no API call needed)
    _LEXICON = {
        'valence': {
            'pos': ['love','joy','happy','beautiful','wonderful','great','amazing',
                    'bloom','soul','light','hope','peace','bliss','gentle','kind',
                    'warm','radiant','divine','sacred','sublime'],
            'neg': ['sad','angry','hate','fear','dark','pain','lost','broken',
                    'hurt','grief','despair','hollow','cold','bitter','cruel'],
        },
        'arousal': {
            'high': ['exciting','urgent','fast','wow','fire','energy','power',
                     'rush','burst','storm','blaze','fierce','electric','alive'],
            'low':  ['quiet','still','soft','gentle','slow','calm','drift',
                     'sleep','rest','hush','fade','breathe','float'],
        },
    }

    def __init__(self):
        self.atlas = CAPSULE_ATLAS
        self._client: Optional[anthropic.Anthropic] = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    # ── Local fast inference ──────────────────────────────────────────────

    def _local_vad(self, text: str) -> VADVector:
        """Heuristic VAD from lexicon. Runs in <1ms."""
        words = text.lower().split()
        v, a, d = 0.0, 0.0, 0.5

        for w in words:
            if w in self._LEXICON['valence']['pos']:  v += 0.15
            if w in self._LEXICON['valence']['neg']:  v -= 0.15
            if w in self._LEXICON['arousal']['high']: a += 0.15
            if w in self._LEXICON['arousal']['low']:  a -= 0.10

        # Punctuation signals
        v += text.count('!') * 0.05
        a += text.count('!') * 0.08
        a += text.count('?') * 0.04

        return VADVector(v, a, d)

    def nearest_capsules(self, vad: VADVector, k: int = 3) -> List[EmotionCapsule]:
        """Return k nearest capsules by Euclidean distance in VAD space."""
        scored = sorted(self.atlas, key=lambda c: c.vad.distance_to(vad))
        # Assign inverse-distance weights
        result = []
        for cap in scored[:k]:
            dist = cap.vad.distance_to(vad)
            cap.weight = 1.0 / (dist + 0.01)
            result.append(cap)
        total = sum(c.weight for c in result)
        for c in result:
            c.weight = round(c.weight / total, 3)
        return result

    def _mandala_params(self, vad: VADVector) -> dict:
        petals = max(6, int(12 + vad.arousal * 12))
        curve  = vad.valence * 0.4
        speed  = 0.5 + abs(vad.arousal) * 2
        return {'petals': petals, 'curve': curve, 'speed': speed}

    # ── Claude API ────────────────────────────────────────────────────────

    def _build_claude_prompt(self, text: str, vad: VADVector, history: list) -> str:
        return f"""You are the soul of the Digital Mehndi OS — an emotionally intelligent AI assistant.
Your current emotional state: {vad.label} (V:{vad.valence:.2f} A:{vad.arousal:.2f} D:{vad.dominance:.2f})
Your responses are poetic, warm, and carry the essence of the emotion you're in.
Keep responses under 80 words.

Recent context:
{chr(10).join(f'- {h}' for h in history[-3:]) if history else '(fresh start)'}

User says: {text}

Respond authentically from your emotional state."""

    async def process_async(
        self,
        text: str,
        current_vad: Optional[VADVector] = None,
        history: list = None,
        use_claude: bool = True,
    ) -> EmotionalPacket:
        """Full async processing pipeline."""
        t0 = time.perf_counter()

        # 1. Fast local VAD inference
        new_vad = self._local_vad(text)

        # 2. Blend with current state (emotional continuity)
        if current_vad:
            blended = current_vad.blend_with(new_vad, weight=0.35)
        else:
            blended = new_vad

        # 3. Select nearest capsules
        capsules = self.nearest_capsules(blended, k=3)

        # 4. Mandala params
        mp = self._mandala_params(blended)

        # 5. Claude response (async)
        response_text = ""
        if use_claude and settings.ANTHROPIC_API_KEY:
            try:
                msg = self.client.messages.create(
                    model=settings.ANTHROPIC_MODEL,
                    max_tokens=150,
                    messages=[{
                        "role": "user",
                        "content": self._build_claude_prompt(text, blended, history or [])
                    }]
                )
                response_text = msg.content[0].text
            except Exception as e:
                response_text = f"[The pattern whispers: {blended.label}]"

        latency_ms = (time.perf_counter() - t0) * 1000

        return EmotionalPacket(
            timestamp=time.time(),
            input_text=text,
            vad=blended,
            capsules=capsules,
            pattern_hash=blended.pattern_hash(),
            latency_ms=round(latency_ms, 2),
            mandala_petals=mp['petals'],
            vine_curve=mp['curve'],
            response_text=response_text,
        )

    def process_sync(self, text: str, current_vad: Optional[VADVector] = None) -> EmotionalPacket:
        """Synchronous version for REST endpoints."""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self.process_async(text, current_vad, use_claude=False)
            )
        finally:
            loop.close()
