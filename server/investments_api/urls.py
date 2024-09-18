from django.urls import path
from . import views
from .views import (
    UserCreate, UserListView, UserDetailView, InvestmentAccountDetailView,
    UserInvestmentAccountListCreateView, UserInvestmentAccountDetailView,
    TransactionListCreateAPIView, TransactionRetrieveUpdateDestroyAPIView,
    AdminUserTransactionListAPIView
)

urlpatterns = [
    # Group
    path('groups/', views.GroupsListCreateView.as_view(), name='group-list-create'),
    path('groups/<int:pk>/', views.GroupsDetailView.as_view(), name='group-detail'),

    path('users/register/', UserCreate.as_view(), name='user-create'),
    path('users/', UserListView.as_view(), name='users-list'),
    path('users/<uuid:pk>/', UserDetailView.as_view(), name='user-detail'),

    path('investment-accounts/register/', views.InvestmentAccountCreateView.as_view(), name='investment-account-create'),
    path('investment-accounts/', views.InvestmentAccountListView.as_view(), name='investment-account-list'),
    path('investment-accounts/<uuid:pk>/', InvestmentAccountDetailView.as_view(), name='investment-account-detail'),

    path('user-investment-accounts/', UserInvestmentAccountListCreateView.as_view(), name='user-investment-account-list-create'),
    path('user-investment-accounts/<uuid:pk>/', UserInvestmentAccountDetailView.as_view(), name='user-investment-account-detail'),

    path('admin/users/<uuid:user_id>/transactions/', AdminUserTransactionListAPIView.as_view(), name='admin-user-transactions'),

    path('investment-accounts/<uuid:account_id>/transactions/', TransactionListCreateAPIView.as_view(), name='transaction-list-create'),
    path('investment-accounts/<uuid:account_id>/transactions/<uuid:pk>/', TransactionRetrieveUpdateDestroyAPIView.as_view(), name='transaction-detail'),
]