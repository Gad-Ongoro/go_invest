from django.contrib.auth.models import Group
from rest_framework import generics, response, status
from django.db.models import Sum, F, Case, When
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied
from django.utils.dateparse import parse_date
from .models import User, InvestmentAccount, UserInvestmentAccount, Transaction
from . import serializers
from .serializers import (
    UserSerializer, InvestmentAccountSerializer, 
    UserInvestmentAccountSerializer, TransactionSerializer
)
from .permissions import TransactionPermission

# Groups
class GroupsListCreateView(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = [IsAdminUser]
    
    
class GroupsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = [IsAdminUser]

# User Views
class UserCreate(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# Investment Account Views
class InvestmentAccountCreateView(generics.CreateAPIView):
    queryset = InvestmentAccount.objects.all()
    serializer_class = InvestmentAccountSerializer
    permission_classes = [IsAdminUser]

class InvestmentAccountListView(generics.ListAPIView):
    queryset = InvestmentAccount.objects.all()
    serializer_class = InvestmentAccountSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class InvestmentAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InvestmentAccount.objects.all()
    serializer_class = InvestmentAccountSerializer
    permission_classes = [IsAdminUser]

# User Investment Account Views
class UserInvestmentAccountListCreateView(generics.ListCreateAPIView):
    queryset = UserInvestmentAccount.objects.all()
    serializer_class = UserInvestmentAccountSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        user_investment_account = serializer.save()

        user = user_investment_account.user
        investment_account = user_investment_account.investment_account

        if investment_account.permission == InvestmentAccount.VIEW:
            group_name = 'view_group'
        elif investment_account.permission == InvestmentAccount.FULL_CRUD:
            group_name = 'crud_group'
        elif investment_account.permission == InvestmentAccount.POST_ONLY:
            group_name = 'create_group'
        else:
            group_name = None

        if group_name:
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            user.save()

class UserInvestmentAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserInvestmentAccount.objects.all()
    serializer_class = UserInvestmentAccountSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def perform_destroy(self, instance):
        user = instance.user
        investment_account = instance.investment_account

        if investment_account.permission == InvestmentAccount.VIEW:
            group_name = 'view_group'
        elif investment_account.permission == InvestmentAccount.FULL_CRUD:
            group_name = 'crud_group'
        elif investment_account.permission == InvestmentAccount.POST_ONLY:
            group_name = 'create_group'
        else:
            group_name = None

        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                user.groups.remove(group)
                user.save()
            except Group.DoesNotExist:
                print(f'Group {group_name} does not exist')

        super().perform_destroy(instance)

# Transaction Views
class TransactionListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, TransactionPermission]

    def get_queryset(self):
        account_id = self.kwargs.get('account_id')
        return Transaction.objects.filter(account=account_id)

    def create(self, request, *args, **kwargs):
        account_id = self.kwargs.get('account_id')
        if not UserInvestmentAccount.objects.filter(user=request.data.get('user'), investment_account_id=account_id).exists():
            raise PermissionDenied("You do not have permission to make transactions in this account.")
        return super().create(request, *args, **kwargs)

class TransactionRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [TransactionPermission]

    def get_queryset(self):
        account_id = self.kwargs.get('account_id')
        return Transaction.objects.filter(account_id=account_id)
    
# admin (user transactions & date range filter)
class AdminUserTransactionListAPIView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        queryset = Transaction.objects.filter(user=user_id)

        # date range filter
        if start_date:
            start_date = parse_date(start_date)
            start_date = timezone.make_aware(timezone.datetime.combine(start_date, timezone.datetime.min.time()))
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            end_date = parse_date(end_date)
            end_date = timezone.make_aware(timezone.datetime.combine(end_date, timezone.datetime.max.time()))
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # total balance
        balance_aggregation = queryset.aggregate(
            total_credits=Sum(Case(
                When(transaction_type='credit', then=F('amount')),
                default=0,
            )),
            total_debits=Sum(Case(
                When(transaction_type='debit', then=F('amount')),
                default=0,
            ))
        )

        total_balance = (balance_aggregation['total_credits'] or 0) - (balance_aggregation['total_debits'] or 0)

        response_data = {
            'transactions': self.get_serializer(queryset, many=True).data,
            'total_balance': total_balance
        }

        return response.Response(response_data, status=status.HTTP_200_OK)