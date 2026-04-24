from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('category/<str:category>/', views.category_view, name='category'),
    path('category/<str:category>/class/<int:class_id>/', views.class_subjects, name='class_subjects'),
    path('category/<str:category>/class/<int:class_id>/subject/<int:subject_id>/', views.subject_files, name='subject_files'),
    path('contact/', views.contact_view, name='contact'),
    path('search/', views.search_files, name='search'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/upload/', views.upload_pdf, name='upload_pdf'),
    path('dashboard/edit/<int:pk>/', views.edit_pdf, name='edit_pdf'),
    path('dashboard/delete/<int:pk>/', views.delete_pdf, name='delete_pdf'),
    path('live-search/', views.live_search, name='live_search'),
    path('files/<int:id>/', views.file_detail, name='file_detail'),
    path('load-subjects/', views.load_subjects, name='load_subjects'),
    path('achievers/', views.all_achievers, name='all_achievers'),
    path('download/<int:file_id>/', views.download_file, name='download_file'),  # ← simplified
    path('robots.txt', views.robots_txt),
]