from rest_framework import serializers
from django.contrib.auth.models import Group
from .models import User, InvestmentAccount, UserInvestmentAccount, Transaction

# Groups
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

# User-Investment Accounts
class UserInvestmentAccountSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='email', queryset=User.objects.all())
    investment_account = serializers.SlugRelatedField(slug_field='name', queryset=InvestmentAccount.objects.all())

    class Meta:
        model = UserInvestmentAccount
        fields = ['id', 'user', 'investment_account']

# Users
class UserSerializer(serializers.ModelSerializer):
    accounts = UserInvestmentAccountSerializer(source='userinvestmentaccount_set', many=True, read_only=True)
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'password', 'accounts', 'date_joined', 'updated_at']
        extra_kwargs = {'password': {'write_only': True}, 'date_joined': {'read_only': True}}
        
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

# Investment Accounts
class InvestmentAccountSerializer(serializers.ModelSerializer):
    users = UserInvestmentAccountSerializer(source='userinvestmentaccount_set', many=True, read_only=True)

    class Meta:
        model = InvestmentAccount
        fields = ['id', 'name', 'description', 'users', 'permission', 'transactions', 'created_at', 'updated_at']

# Transactions
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'