from django.urls import path

from . import views

urlpatterns = [
        # path('', views.index, name='index'),
        path('matching/lost', views.lost_matching, name='lost-matching'),
        path('matching/findear', views.findear_matching, name='findear-matching'),
        # path('process', views.process, name='process'),
]
