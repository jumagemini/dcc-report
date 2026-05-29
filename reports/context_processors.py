# reports/context_processors.py
from .models import UserProfile, Notification

def user_dccs(request):
    if request.user.is_authenticated:
        profile = UserProfile.objects.filter(user=request.user).first()
        dccs = profile.allowed_dccs.all().order_by('name') if profile else []
    else:
        dccs = []
    return {'user_dccs': dccs}

def unread_notifications(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_notifications': count}
    return {'unread_notifications': 0}