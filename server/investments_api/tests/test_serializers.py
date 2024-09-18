from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.exceptions import ValidationError
from investments_api.models import InvestmentAccount, UserInvestmentAccount, Transaction
from investments_api.serializers import (
    GroupSerializer, UserInvestmentAccountSerializer,
    UserSerializer, InvestmentAccountSerializer, TransactionSerializer
)

User = get_user_model()

class SerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name='Unique', 
            last_name='User', 
            email='uniqueuser@gmail.com', 
            password='UniquePassword'
        )
        self.investment_account = InvestmentAccount.objects.create(
            name='Investment Account 2',
            description='FULL CRUD Transaction Access Rights to Users',
            permission=InvestmentAccount.VIEW
        )
        self.user_investment_account = UserInvestmentAccount.objects.create(
            user=self.user, investment_account=self.investment_account
        )
        self.transaction = Transaction.objects.create(
            user=self.user, 
            account=self.investment_account, 
            amount=500, 
            description='Initial Deposit', 
            transaction_type='credit'
        )

    def test_group_serializer(self):
        group = Group.objects.create(name='crud_group')
        serializer = GroupSerializer(group)
        self.assertEqual(serializer.data['name'], 'crud_group')

    def test_user_investment_account_serializer(self):
        serializer = UserInvestmentAccountSerializer(self.user_investment_account)
        self.assertEqual(serializer.data['user'], 'uniqueuser@gmail.com')
        self.assertEqual(serializer.data['investment_account'], 'Investment Account 2')

    def test_user_serializer(self):
        serializer = UserSerializer(self.user)
        self.assertEqual(serializer.data['email'], 'uniqueuser@gmail.com')
        self.assertEqual(len(serializer.data['accounts']), 1)
        self.assertEqual(serializer.data['accounts'][0]['investment_account'], 'Investment Account 2')

    def test_user_serializer_create(self):
        data = {
            'first_name':'John', 
            'last_name':'Doe', 
            'email':'johndoe@gmail.com', 
            'password':'UniquePassword'
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.email, 'johndoe@gmail.com')
        self.assertTrue(user.check_password('UniquePassword'))

    def test_investment_account_serializer(self):
        serializer = InvestmentAccountSerializer(self.investment_account)
        self.assertEqual(serializer.data['name'], 'Investment Account 2')
        self.assertEqual(serializer.data['description'], 'FULL CRUD Transaction Access Rights to Users')
        self.assertEqual(len(serializer.data['users']), 1)

    def test_transaction_serializer(self):
        serializer = TransactionSerializer(self.transaction)
        self.assertEqual(serializer.data['amount'], 500)
        self.assertEqual(serializer.data['transaction_type'], 'credit')

    def test_transaction_serializer_create(self):
        data = {
            'user': self.user.id,
            'account': self.investment_account.id,
            'amount': 300,
            'description': 'Second Deposit',
            'transaction_type': 'credit'
        }
        serializer = TransactionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        transaction = serializer.save()
        self.assertEqual(transaction.amount, 300)
        self.assertEqual(transaction.description, 'Second Deposit')

    def test_invalid_user_investment_account_serializer(self):
        data = {
            'user': 'anonymous@gmail.com',
            'investment_account': 'Investment Account X'
        }
        serializer = UserInvestmentAccountSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_invalid_transaction_serializer(self):
        data = {
            'user': self.user.id,
            'account': self.investment_account.id,
            'amount': -100,
            'transaction_type': 'debit'
        }
        serializer = TransactionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
