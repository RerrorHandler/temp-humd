from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import TempData, HumidityData
import json
from django.core.serializers import serialize
from datetime import datetime, timedelta
from django.db.models import Q
from django.utils.timezone import make_aware
from django.utils import timezone
from django.db.models import Avg
from django.views.decorators.http import require_GET




@csrf_exempt
def receive_data(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        board_name = data.get('board_name', 'Arduino')

        TempData.objects.create(board_name=board_name, measure='temperature', data=temperature)
        HumidityData.objects.create(board_name=board_name, measure='humidity', data=humidity)

        return JsonResponse({'status': 'success'}, status=201)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


def home(request):
    return render(request, 'home.html')



@require_GET
def temperature_data_api(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)

        # Получение данных о температуре для каждого уникального board_name
        board_names = TempData.objects.values_list('board_name', flat=True).distinct()
        temperature_data = []

        for board_name in board_names:
            board_data = TempData.objects.filter(board_name=board_name, created_at__range=(start_date, end_date)) \
                                         .annotate(avg_temp=Avg('data')) \
                                         .order_by('created_at')

            timestamps = [data.created_at.isoformat() for data in board_data]
            temperatures = [data.avg_temp if data.avg_temp else 'null' for data in board_data]
            
            temperature_data.append({
                'board_name': board_name,
                'timestamps': timestamps,
                'temperatures': temperatures,
            })

        return JsonResponse({'temperature_data': temperature_data})

    return JsonResponse({'error': 'Invalid request parameters'})