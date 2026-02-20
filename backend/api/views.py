"""
🌸 Digital Mehndi OS — REST API Views
"""
import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from emotional_kernel.kernel import EmotionalKernel, VADVector
from memory.models import EmotionMemory, EmotionalProfile


kernel = EmotionalKernel()


@method_decorator(csrf_exempt, name='dispatch')
class ProcessEmotionView(View):
    """POST /api/emotion/process/ — sync REST endpoint for emotion processing."""

    def post(self, request):
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        text = body.get('text', '').strip()
        if not text:
            return JsonResponse({'error': 'text is required'}, status=400)

        current_vad = None
        if 'vad' in body:
            v = body['vad']
            current_vad = VADVector(
                v.get('valence', 0.0),
                v.get('arousal', 0.0),
                v.get('dominance', 0.5),
            )

        packet = kernel.process_sync(text, current_vad)
        return JsonResponse({'status': 'ok', 'packet': packet.to_dict()})


class EmotionHistoryView(View):
    """GET /api/emotion/history/?user_id=&limit=20"""

    def get(self, request):
        user_id = request.GET.get('user_id', 'default')
        limit   = min(int(request.GET.get('limit', 20)), 100)
        memories = EmotionMemory.objects.filter(user_id=user_id)[:limit]
        return JsonResponse({
            'user_id': user_id,
            'count': memories.count(),
            'memories': [m.to_dict() for m in memories],
        })


class EmotionalProfileView(View):
    """GET /api/profile/<user_id>/"""

    def get(self, request, user_id='default'):
        profile, _ = EmotionalProfile.objects.get_or_create(user_id=user_id)
        return JsonResponse({'status': 'ok', 'profile': profile.to_dict()})


class HealthView(View):
    """GET /api/health/"""
    def get(self, request):
        return JsonResponse({
            'status': 'alive',
            'system': 'Digital Mehndi OS',
            'version': '1.0.0',
            'kernel': 'EmotionalKernel v1',
        })
