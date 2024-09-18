from django.test import TestCase
from django.contrib.auth import get_user_model
from investments_api.models import InvestmentAccount, UserInvestmentAccount, Transaction

User = get_user_model()

class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            first_name='Unique', 
            last_name='User', 
            email='uniqueuser@gmail.com', 
            password='UniquePassword'
        )
        self.assertEqual(user.email, 'uniqueuser@gmail.com')
        self.assertTrue(user.check_password('UniquePassword'))
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(email='admin@gmail.com', password='Admin123')
        self.assertEqual(superuser.email, 'admin@gmail.com')
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)

# Investment Account
class InvestmentAccountModelTest(TestCase):
    def test_create_investment_account(self):
        account = InvestmentAccount.objects.create(
            name='Investment Account 1',
            description='Read-Only Transaction Access Rights to Normal Users',
            permission=InvestmentAccount.VIEW
        )
        self.assertEqual(account.name, 'Investment Account 1')
        self.assertEqual(account.permission, InvestmentAccount.VIEW)

    def test_account_permissions(self):
        account = InvestmentAccount.objects.create(
            name='Investment Account 2',
            description='FULL CRUD Transaction Access Rights to Users',
            permission=InvestmentAccount.FULL_CRUD
        )
        self.assertEqual(account.name, 'Investment Account 2')
        self.assertEqual(account.permission, InvestmentAccount.FULL_CRUD)

# User-Investment Account
class UserInvestmentAccountModelTest(TestCase):
    def test_user_investment_account_association(self):
        user = User.objects.create_user(
            first_name='Unique', 
            last_name='User', 
            email='uniqueuser@gmail.com', 
            password='UniquePassword'
        )
        account = InvestmentAccount.objects.create(
            name='Investment Account 1',
            description='Read-Only Transaction Access Rights to Normal Users',
            permission=InvestmentAccount.VIEW
        )
        user_account = UserInvestmentAccount.objects.create(user=user, investment_account=account)
        self.assertEqual(user_account.user, user)
        self.assertEqual(user_account.investment_account, account)

# Transaction
class TransactionModelTest(TestCase):
    def test_create_transaction(self):
        user = User.objects.create_user(
            first_name='Unique', 
            last_name='User', 
            email='uniqueuser@gmail.com', 
            password='UniquePassword'
        )
        account = InvestmentAccount.objects.create(
            name='Investment Account 2',
            description='FULL CRUD Transaction Access Rights to Users',
            permission=InvestmentAccount.FULL_CRUD
        )
        transaction = Transaction.objects.create(
            user=user,
            account=account,
            amount=100,
            transaction_type='credit',
            description='Initial Deposit'
        )
        self.assertEqual(transaction.amount, 100)
        self.assertEqual(transaction.transaction_type, 'credit')
        self.assertTrue(transaction.is_credit)
        self.assertFalse(transaction.is_debit)

    # property test
    def test_transaction_debit(self):
        user = User.objects.create_user(
            first_name='Unique', 
            last_name='User', 
            email='uniqueuser@gmail.com', 
            password='UniquePassword'
        )
        account = InvestmentAccount.objects.create(
            name='Investment Account 2',
            description='FULL CRUD Transaction Access Rights to Users',
            permission=InvestmentAccount.FULL_CRUD
        )
        transaction = Transaction.objects.create(
            user=user,
            account=account,
            amount=50,
            transaction_type='debit',
            description='Withrawal'
        )
        self.assertEqual(transaction.amount, 50)
        self.assertTrue(transaction.is_debit)
        self.assertFalse(transaction.is_credit)
