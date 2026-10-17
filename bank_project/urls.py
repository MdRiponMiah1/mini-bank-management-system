from django.contrib import admin
from django.urls import include, path

from customers.views import ProfileView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/auth/', include('customers.urls')),
    path('api/profile/', ProfileView.as_view(), name='profile-api'),
    path('api/accounts/', include('accounts.urls')),
    path('api/transactions/', include('transactions.urls')),
]
