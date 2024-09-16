from django.contrib import admin
from .models import User, InvestmentAccount, UserInvestmentAccount, Transaction

# Register your models here.

admin.site.register(User)
admin.site.register(InvestmentAccount)
admin.site.register(UserInvestmentAccount)
admin.site.register(Transaction)