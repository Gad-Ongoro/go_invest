from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from .models import InvestmentAccount, UserInvestmentAccount, User
from django.core.exceptions import ValidationError
import uuid

class TransactionPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        transaction_data = request.data
        user_id = transaction_data.get('user')
        user = user_id if user_id else request.user
        account_id = view.kwargs.get('account_id')

        if not account_id:
            return False

        # Membership restriction
        try:
            def get_user_by_email_or_id(user_identifier):
                if isinstance(user_identifier, User):
                    return user_identifier
                try:
                    uuid_obj = uuid.UUID(str(user_identifier), version=4)
                    user = User.objects.get(id=uuid_obj)
                except (ValueError, TypeError, ValidationError):
                    user = User.objects.get(email=user_identifier)
                return user

            user_investment = UserInvestmentAccount.objects.get(user=get_user_by_email_or_id(user), investment_account=account_id)
            account = user_investment.investment_account
            user = get_user_by_email_or_id(user)
            user_groups = user.groups.all()
            user_access_rights = [group.permissions.all()[0].codename for group in user.groups.all()]

            if account.permission == InvestmentAccount.VIEW and 'can_only_read_transactions' in user_access_rights:
                return request.method == 'GET' and user_groups.filter(name='view_group').exists()
            elif account.permission == InvestmentAccount.FULL_CRUD and 'can_crud_transactions' in user_access_rights:
                return user_groups.filter(name='crud_group').exists()
            elif account.permission == InvestmentAccount.POST_ONLY and 'can_only_create_transactions' in user_access_rights:
                return request.method == 'POST' and user_groups.filter(name='create_group').exists()
            else:
                raise PermissionDenied(detail='You do not have permission to perform this action.')

        except UserInvestmentAccount.DoesNotExist:
            raise PermissionDenied(detail='You are not a member of this investment account.')

    def has_object_permission(self, request, view, obj):
        user = request.user
        account_id = obj.account.id

        # Membership restriction
        try:
            user_investment = UserInvestmentAccount.objects.get(user=user, investment_account_id=account_id)
            account = user_investment.investment_account

            user_groups = user.groups.all()

            if account.permission == InvestmentAccount.VIEW:
                return request.method == 'GET' and user_groups.filter(name='view_group').exists()
            elif account.permission == InvestmentAccount.FULL_CRUD:
                return user_groups.filter(name='crud_group').exists()
            elif account.permission == InvestmentAccount.POST_ONLY:
                return request.method == 'POST' and user_groups.filter(name='create_group').exists()

        except UserInvestmentAccount.DoesNotExist:
            raise PermissionDenied(detail='You are not a member of this investment account.')

        return False