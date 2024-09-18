from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from investments_api.models import InvestmentAccount, UserInvestmentAccount, Transaction
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class TransactionAPIPermissionsTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # users
        self.user1 = User.objects.create_user(first_name='John', last_name='Doe', email='johndoe@gmail.com', password='JohnDoe123')
        self.user2 = User.objects.create_user(first_name='Jane', last_name='Doe', email='janedoe@gmail.com', password='JaneDoe123')
        self.user3 = User.objects.create_user(first_name='Josh', last_name='Doe', email='joshdoe@gmail.com', password='JoshDoe123')

        # permissions
        transaction_content_type = ContentType.objects.get_for_model(InvestmentAccount)
        view_permission, _ = Permission.objects.get_or_create(
            codename='can_only_read_transactions', 
            name='Can only view transactions',
            content_type=transaction_content_type
        )
        create_permission, _ = Permission.objects.get_or_create(
            codename='can_only_create_transactions',
            name='Can only create transactions',
            content_type=transaction_content_type
        )
        crud_permission, _ = Permission.objects.get_or_create(
            codename='can_crud_transactions', 
            name='Can CRUD transactions',
            content_type=transaction_content_type
        )
        
        # assign permissions to groups
        self.view_group = Group.objects.create(name='view_group')
        self.view_group.permissions.add(view_permission)

        self.create_group = Group.objects.create(name='create_group')
        self.create_group.permissions.add(create_permission)

        self.crud_group = Group.objects.create(name='crud_group')
        self.crud_group.permissions.add(crud_permission)

        # investment accounts
        self.account1 = InvestmentAccount.objects.create(name="Investment Account 1", permission=InvestmentAccount.VIEW)
        self.account2 = InvestmentAccount.objects.create(name="Investment Account 2", permission=InvestmentAccount.FULL_CRUD)
        self.account3 = InvestmentAccount.objects.create(name="Investment Account 3", permission=InvestmentAccount.POST_ONLY)

        # UserInvestmentAccount using perform_create logic
        self.create_user_investment_account(self.user1, self.account1) # user1 ~ view only
        self.create_user_investment_account(self.user2, self.account2) # user2 ~ full crud
        self.create_user_investment_account(self.user3, self.account3) # user3 ~ post only

        # transactions
        self.transaction1 = Transaction.objects.create(user=self.user1, account=self.account1, amount=100, description="Transaction 1", transaction_type='credit')
        self.transaction2 = Transaction.objects.create(user=self.user2, account=self.account2, amount=200, description="Transaction 2", transaction_type='debit')

    def create_user_investment_account(self, user, investment_account):
        user_investment_account = UserInvestmentAccount.objects.create(user=user, investment_account=investment_account)
        # print(user_investment_account)

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
            
    def test_user1_has_correct_permissions(self): # view only
        self.assertIn(self.view_group, self.user1.groups.all())
        self.assertNotIn(self.crud_group, self.user1.groups.all())
        self.assertNotIn(self.create_group, self.user1.groups.all())

    def test_user2_has_full_crud_permissions(self): # full crud
        self.assertIn(self.crud_group, self.user2.groups.all())
        self.assertNotIn(self.view_group, self.user2.groups.all())
        self.assertNotIn(self.create_group, self.user2.groups.all())
        
    # user1 ~ GET only
    def test_user1_can_only_view_transactions(self):
        refresh = RefreshToken.for_user(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(refresh.access_token))

        # allows GET request
        response = self.client.get(reverse('transaction-list-create', kwargs={'account_id': self.account1.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # no CREATE access
        response = self.client.post(reverse('transaction-list-create', kwargs={'account_id': self.account1.id}), data={
            'user': self.user1.id,
            'account': self.account1.id,
            'amount': 500,
            'description': 'Invalid transaction by user1',
            'transaction_type': 'credit'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # no UPDATE access
        response = self.client.patch(reverse('transaction-detail', kwargs={'account_id': self.account1.id, 'pk': self.transaction1.id}), data={
            'amount': 1000
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # no DELETE access
        response = self.client.delete(reverse('transaction-detail', kwargs={'account_id': self.account1.id, 'pk': self.transaction1.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # user2 ~ full crud
    def test_user2_has_full_crud_permissions(self):
        refresh = RefreshToken.for_user(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(refresh.access_token))
        
        # allows GET request
        response = self.client.get(reverse('transaction-list-create', kwargs={'account_id': self.account2.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # allows POST request
        response = self.client.post(reverse('transaction-list-create', kwargs={'account_id': self.account2.id}), data={
            'user': self.user2.id,
            'account': self.account2.id,
            'amount': 500,
            'description': 'Valid transaction by user2',
            'transaction_type': 'credit'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # allows UPDATE request
        response = self.client.patch(reverse('transaction-detail', kwargs={'account_id': self.account2.id, 'pk': self.transaction2.id}), data={
            'amount': 1000
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
        # allows DELETE request
        response = self.client.delete(reverse('transaction-detail', kwargs={'account_id': self.account2.id, 'pk': self.transaction2.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # user3 ~ CREATE only
    def test_user3_can_only_create_transactions(self):
        refresh = RefreshToken.for_user(self.user3)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(refresh.access_token))

        # no GET access
        response = self.client.get(reverse('transaction-list-create', kwargs={'account_id': self.account3.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # allows POST request
        response = self.client.post(reverse('transaction-list-create', kwargs={'account_id': self.account3.id}), data={
            'user': self.user3.id,
            'account': self.account3.id,
            'amount': 300,
            'description': 'Valid transaction by user3',
            'transaction_type': 'credit'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # no UPDATE access
        response = self.client.patch(reverse('transaction-detail', kwargs={'account_id': self.account3.id, 'pk': self.transaction1.id}), data={
            'amount': 1000
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # no DELETE access
        response = self.client.delete(reverse('transaction-detail', kwargs={'account_id': self.account3.id, 'pk': self.transaction1.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # non-member test
    def test_non_member_user_cannot_access_account(self):
        non_member_user = User.objects.create_user(first_name='Sean', last_name='Smith', email='seansmith@gmail.com', password='SeanSmith123')

        self.client.force_authenticate(user=non_member_user)

        # no GET access
        response = self.client.get(reverse('transaction-list-create', kwargs={'account_id': self.account1.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # no POST access
        response = self.client.post(reverse('transaction-list-create', kwargs={'account_id': self.account1.id}), data={
            'user': non_member_user.id,
            'account': self.account1.id,
            'amount': 1000,
            'description': 'Unauthorized transaction',
            'transaction_type': 'credit'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
