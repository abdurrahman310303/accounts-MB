from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('accounts/', views.accounts_list, name='accounts_list'),
    path('accounts/<int:account_id>/', views.account_detail, name='account_detail'),
    path('accounts/add/', views.add_account, name='add_account'),
    path('accounts/<int:account_id>/edit/', views.edit_account, name='edit_account'),
    path('accounts/<int:account_id>/delete/', views.delete_account, name='delete_account'),
    path('transactions/', views.transactions_list, name='transactions_list'),
    path('transactions/add/', views.add_transaction, name='add_transaction'),
    path('transactions/<int:transaction_id>/', views.view_transaction, name='view_transaction'),
    path('transactions/<int:transaction_id>/edit/', views.edit_transaction, name='edit_transaction'),
    path('transactions/<int:transaction_id>/delete/', views.delete_transaction, name='delete_transaction'),
    path('categories/', views.categories_list, name='categories_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    path('teams/', views.teams_list, name='teams_list'),
    path('teams/<int:team_id>/', views.team_detail, name='team_detail'),
    path('teams/add/', views.add_team, name='add_team'),
    path('teams/<int:team_id>/edit/', views.edit_team, name='edit_team'),
    path('teams/<int:team_id>/delete/', views.delete_team, name='delete_team'),
    path('reports/', views.reports, name='reports'),
    path('exchange-rates/update/', views.update_exchange_rates, name='update_exchange_rates'),
]
