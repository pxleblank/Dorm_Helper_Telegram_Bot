from django.shortcuts import render

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import User


def unverified_users(request):
    users = User.objects.filter(is_verified=False, is_blocked=False).values('id', 'full_name', 'room_number',
                                                                            'pass_photo')
    return JsonResponse(list(users), safe=False)


@csrf_exempt
def verify_user(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if user:
        user.is_verified = True
        user.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'User not found'})


@csrf_exempt
def delete_user(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if user:
        user.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'User not found'})
