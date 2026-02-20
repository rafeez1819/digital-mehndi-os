"""
🌸 Digital Mehndi OS — Memory Models
SQLite-backed emotion history & pattern memory
"""
from django.db import models
import json


class EmotionMemory(models.Model):
    """
    Every interaction is woven into permanent memory.
    The system remembers every emotional thread.
    """
    user_id       = models.CharField(max_length=128, default='default', db_index=True)
    timestamp     = models.DateTimeField(auto_now_add=True, db_index=True)
    input_text    = models.TextField()
    response_text = models.TextField(blank=True)

    # VAD values
    valence       = models.FloatField()
    arousal       = models.FloatField()
    dominance     = models.FloatField()

    # Derived
    emotion_label = models.CharField(max_length=32)
    pattern_hash  = models.CharField(max_length=64)
    latency_ms    = models.FloatField(default=0)

    # Capsule data (JSON)
    capsules_json = models.TextField(default='[]')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Emotion Memory'
        verbose_name_plural = 'Emotion Memories'

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.emotion_label} — {self.input_text[:40]}"

    @property
    def capsules(self):
        return json.loads(self.capsules_json)

    @property
    def vad_tuple(self):
        return (self.valence, self.arousal, self.dominance)

    def to_dict(self):
        return {
            'id': self.pk,
            'timestamp': self.timestamp.isoformat(),
            'input_text': self.input_text,
            'response_text': self.response_text,
            'vad': {'valence': self.valence, 'arousal': self.arousal, 'dominance': self.dominance},
            'emotion_label': self.emotion_label,
            'pattern_hash': self.pattern_hash,
            'latency_ms': self.latency_ms,
            'capsules': self.capsules,
        }


class EmotionalProfile(models.Model):
    """
    Per-user emotional baseline — the fingerprint of a soul.
    Evolves over time through interactions.
    """
    user_id             = models.CharField(max_length=128, unique=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    # Running average VAD
    avg_valence         = models.FloatField(default=0.0)
    avg_arousal         = models.FloatField(default=0.0)
    avg_dominance       = models.FloatField(default=0.5)

    # Peak states
    peak_valence        = models.FloatField(default=0.0)
    peak_arousal        = models.FloatField(default=0.0)

    # Interaction count
    interaction_count   = models.IntegerField(default=0)

    # Dominant emotion label
    dominant_emotion    = models.CharField(max_length=32, default='Neutral')

    class Meta:
        verbose_name = 'Emotional Profile'

    def __str__(self):
        return f"Profile:{self.user_id} — {self.dominant_emotion} ({self.interaction_count} interactions)"

    def update_from_memory(self, memory: EmotionMemory):
        """Rolling update of the emotional profile."""
        n = self.interaction_count
        # Exponential moving average (α = 0.1)
        α = 0.1
        self.avg_valence   = self.avg_valence   * (1 - α) + memory.valence   * α
        self.avg_arousal   = self.avg_arousal   * (1 - α) + memory.arousal   * α
        self.avg_dominance = self.avg_dominance * (1 - α) + memory.dominance * α
        self.peak_valence  = max(self.peak_valence,  abs(memory.valence))
        self.peak_arousal  = max(self.peak_arousal,  abs(memory.arousal))
        self.interaction_count = n + 1
        self.dominant_emotion  = memory.emotion_label
        self.save()

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'avg_vad': {
                'valence':   round(self.avg_valence, 3),
                'arousal':   round(self.avg_arousal, 3),
                'dominance': round(self.avg_dominance, 3),
            },
            'dominant_emotion': self.dominant_emotion,
            'interaction_count': self.interaction_count,
            'updated_at': self.updated_at.isoformat(),
        }
