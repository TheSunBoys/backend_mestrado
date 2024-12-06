from django.urls import path
from .views import register_view, login_view, dashboard_view
from django.contrib.auth.views import LogoutView
from home.views import home
urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('', home, name='home'),

]
