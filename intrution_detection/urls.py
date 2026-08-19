"""intrution_detection URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from . import views
from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',views.first),
    path('index',views.index),
    path('index/',views.index),
    
    path('reg/',views.reg),
    path('reg/addreg',views.addreg),
    path('v_register/',views.v_register),
    path('about', views.about),
    path('login/',views.login),
    path('login/addlogin',views.addlogin),
    path('logout/',views.logout),
    path('fedback',views.fedback),
    path('addfedbk',views.addfedbk),
    path('v_feedback',views.v_feedback),
    path('file',views.file),
    path('addfile',views.addfile),
    path('predict_and_save',views.predict_and_save),
    path('v_addfile',views.v_addfile),
    path('v_addfile_user',views.v_addfile_user),  
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
