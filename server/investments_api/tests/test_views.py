from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from rest_framework import status
from investments_api.models import InvestmentAccount, UserInvestmentAccount, Transaction
from datetime import datetime

User = get_user_model()

class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(email='admin@gmail.com', password='Admin123')
        self.normal_user = User.objects.create_user(
            first_name='Unique',
            last_name='User',
            email='uniqueuser@gmail.com',
            password='UniquePassword'
        )
        self.client.force_authenticate(user=self.admin_user)
        
        self.view_group = Group.objects.create(name='view_group')
        self.crud_group = Group.objects.create(name='crud_group')
        self.create_group = Group.objects.create(name='create_group')

        self.investment_account = InvestmentAccount.objects.create(
            name='Investment Account 2', description='FULL CRUD Transaction Access Rights to Users', permission=InvestmentAccount.FULL_CRUD
        )
        
        self.investment_account_3 = InvestmentAccount.objects.create(
            name='Investment Account 3', description='View-Only Transaction Access Rights to Normal Users', permission=InvestmentAccount.VIEW
        )
        
        self.user_investment_account = UserInvestmentAccount.objects.create(
            user=self.normal_user, investment_account=self.investment_account
        )

        self.transaction = Transaction.objects.create(
            user=self.normal_user, account=self.investment_account, amount=500, description='Initial Deposit', transaction_type='credit'
        )
        
        self.transaction = Transaction.objects.create(
            user=self.normal_user, account=self.investment_account, amount=100, description='Initial Withdrawal', transaction_type='debit'
        )

    def test_group_list_create(self):
        response = self.client.get('/api/groups/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('view_group', [group['name'] for group in response.data])

        response2 = self.client.post('/api/groups/', {'name': 'Group4'})
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 4)
        self.assertTrue(Group.objects.filter(name='Group4').exists())

    def test_group_detail(self):
        response = self.client.get(f'/api/groups/{self.view_group.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'view_group')

    def test_user_create(self):
        response = self.client.post('/api/users/register/', {
            'email': 'johndoe65@gmail.com',
            'password': 'JohnDoe2323#',
            'first_name': 'John',
            'last_name': 'Doe'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='johndoe65@gmail.com').exists())

    def test_user_list(self):
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('uniqueuser@gmail.com', [user['email'] for user in response.data])

    def test_user_detail(self):
        response = self.client.get(f'/api/users/{self.normal_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'uniqueuser@gmail.com')

    def test_investment_account_create(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/investment-accounts/register/', {
            'name': 'Investment Account 4',
            'description': 'Investment Account 4',
            'permission': InvestmentAccount.FULL_CRUD
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(InvestmentAccount.objects.filter(name='Investment Account 4').exists())

    # investment account list
    def test_investment_account_list(self):
        response = self.client.get('/api/investment-accounts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Investment Account 2', [account['name'] for account in response.data])

    def test_user_investment_account_create_and_list(self):
        # create
        response_create = self.client.post('/api/user-investment-accounts/', {
            'user': self.normal_user.email,
            'investment_account': self.investment_account_3.name
        })
        
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserInvestmentAccount.objects.filter(user=self.normal_user, investment_account=self.investment_account).exists())
        
        # list
        response_list = self.client.get('/api/user-investment-accounts/')
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)
        created_user_investment = UserInvestmentAccount.objects.get(user=self.normal_user, investment_account=self.investment_account_3)
        self.assertIn(str(created_user_investment.id), [account['id'] for account in response_list.data])
        
    # user investment detail
    def test_user_investment_account_detail_retrieve_update_destroy(self):
        # retrieve
        response_retrieve = self.client.get(f'/api/user-investment-accounts/{self.user_investment_account.id}/')
        self.assertEqual(response_retrieve.status_code, status.HTTP_200_OK)
        self.assertEqual(response_retrieve.data['id'], str(self.user_investment_account.id))
        self.assertEqual(response_retrieve.data['user'], self.normal_user.email)
        self.assertEqual(response_retrieve.data['investment_account'], self.investment_account.name)

        # update
        response_update = self.client.put(f'/api/user-investment-accounts/{self.user_investment_account.id}/', {
            'user': self.normal_user.email,
            'investment_account': self.investment_account_3.name
        })
        self.assertEqual(response_update.status_code, status.HTTP_200_OK)
        updated_instance = UserInvestmentAccount.objects.get(id=self.user_investment_account.id)
        self.assertEqual(updated_instance.investment_account, self.investment_account_3)

        # destroy
        response_destroy = self.client.delete(f'/api/user-investment-accounts/{self.user_investment_account.id}/')
        self.assertEqual(response_destroy.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserInvestmentAccount.objects.filter(id=self.user_investment_account.id).exists())


    # admin user transactions
    def test_admin_user_transaction_list(self):
        start_date = datetime.now().replace(month=1, day=1).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        response = self.client.get(
            f'/api/admin/users/{self.normal_user.id}/transactions/',
            {'start_date': start_date, 'end_date': end_date}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Initial Deposit', [transaction['description'] for transaction in response.data['transactions']])
        self.assertEqual(response.data['total_balance'], 400)