from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from investments_api.models import InvestmentAccount

class Command(BaseCommand):
    help = 'Create predefined groups and assign permissions'

    def handle(self, *args, **kwargs):
        groups = {
            'view_group': ['can_only_read_transactions'],
            'crud_group': ['can_crud_transactions'],
            'create_group': ['can_only_create_transactions']
        }

        transaction_content_type = ContentType.objects.get_for_model(InvestmentAccount)

        for group_name, permissions in groups.items():
            group, created = Group.objects.get_or_create(name=group_name)

            if created:
                self.stdout.write(self.style.SUCCESS(f'Group "{group_name}" created'))

            for permission_code in permissions:
                permission = Permission.objects.get(codename=permission_code, content_type=transaction_content_type)
                group.permissions.add(permission)

            self.stdout.write(self.style.SUCCESS(f'Permissions assigned to group "{group_name}"'))