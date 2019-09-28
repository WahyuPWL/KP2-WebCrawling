"""project2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from rest_framework import routers, serializers, viewsets
from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns
from webCrawler import views

router = routers.DefaultRouter()
router.register(r'paper', views.paperList)

urlpatterns = [
    path('', include(router.urls),name='home'),
    path('admin/', admin.site.urls),
    path('addSinta/', views.addSinta),
    path('addIeee/', views.addIeee),
    path('addDoaj/', views.addDoaj),
    path('addRg/', views.addRg),
    path('main/', views.Main),
    path('fix/', views.is_need_fixing),
]
