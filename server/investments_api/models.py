from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid

# Create your models here.
# custom user model
class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not password:
            raise ValueError('The Password field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    # uuids as pk for enhanced security
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = None
    accounts = models.ManyToManyField('InvestmentAccount', through='UserInvestmentAccount')
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

# InvestmentAccount
class InvestmentAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(User, through='UserInvestmentAccount')
    
    VIEW = 'can_only_read_transactions'
    FULL_CRUD = 'can_crud_transactions'
    POST_ONLY = 'can_only_create_transactions'

    ACCESS_LEVEL = [
        (VIEW, 'Read Only'),
        (FULL_CRUD, 'Full CRUD'),
        (POST_ONLY, 'Create Only'),
    ]
    
    permission = models.CharField(max_length=50, choices=ACCESS_LEVEL)
    
    class Meta:
        permissions = [
            ("can_only_read_transactions", "Can only view transactions"),
            ("can_crud_transactions", "Can CRUD transactions"),
            ("can_only_create_transactions", "Can only create transactions"),
        ]

    def __str__(self):
        return self.name

# User & InvestmentAccount association table
class UserInvestmentAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    investment_account = models.ForeignKey(InvestmentAccount, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['user', 'investment_account']

    def __str__(self):
        return f'{self.user} - {self.investment_account}'

# transactions
class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey('InvestmentAccount', on_delete=models.CASCADE, related_name='transactions')
    amount = models.IntegerField()
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=10, choices=[('credit', 'Deposit'), ('debit', 'Withdrawal')])

    def __str__(self):
        return f'{self.user} - {self.account} - {self.amount} - {self.transaction_type}'

    @property
    def is_credit(self):
        return self.transaction_type == 'credit'

    @property
    def is_debit(self):
        return self.transaction_type == 'debit'