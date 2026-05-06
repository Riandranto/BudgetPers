from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Transactions
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.transaction_create, name='transaction_create'),
    path('transactions/edit/<int:pk>/', views.transaction_update, name='transaction_update'),
    path('transactions/delete/<int:pk>/', views.transaction_delete, name='transaction_delete'),
    
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/edit/<int:pk>/', views.category_update, name='category_update'),
    path('categories/delete/<int:pk>/', views.category_delete, name='category_delete'),
    
    # Budgets
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/add/', views.budget_create, name='budget_create'),
    path('budgets/edit/<int:pk>/', views.budget_update, name='budget_update'),
    path('budgets/delete/<int:pk>/', views.budget_delete, name='budget_delete'),
    
    # Reports
    path('reports/', views.report_list, name='report_list'),
    
    # Saving Goals
    path('goals/', views.goal_list, name='goal_list'),
    path('goals/add/', views.goal_create, name='goal_create'),
    path('goals/edit/<int:pk>/', views.goal_update, name='goal_update'),
    path('goals/delete/<int:pk>/', views.goal_delete, name='goal_delete'),
    path('goals/add-amount/<int:pk>/', views.goal_add_amount, name='goal_add_amount'),
]