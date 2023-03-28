from django.urls import path

from . import views

urlpatterns = [
	path('test', views.test, name='test'),
    path('submit', views.index, name='index'),
    path('celery_task', views.celery_task, name='celery_task'),
    path('task_images', views.task_images, name='task_images'),
    path('image_layers_rois', views.image_layers_rois, name='image_layers_rois'),
]