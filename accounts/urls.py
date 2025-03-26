from django.urls import path
from .views import login_view
from .views import logout_view
from .views import registro

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('registro/', registro, name='registro'),
]