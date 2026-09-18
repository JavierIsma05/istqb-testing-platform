import os
import sys
import django
sys.path.insert(0, 'D:\\PYTHON\\iSTQB_Testing_Platform\\src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.testcases.models import TestCase
from apps.core.permissions import visible_projects_for

User = get_user_model()
user = User.objects.filter(role=User.Roles.STUDENT).first()
print('Student user:', user)

if user:
    client = Client()
    client.force_login(user)
    projects = visible_projects_for(user)
    test_cases = TestCase.objects.filter(test_plan__project__in=projects).first()
    print('Test case:', test_cases)
    if test_cases:
        response = client.get('/executions/?case=' + str(test_cases.id))
        print('Status:', response.status_code)
        content = response.content.decode('utf-8')
        if 'col-lg-7' in content and 'col-lg-5' in content:
            print('Column classes found')
        if 'w-100' in content:
            print('w-100 class found in form fields')
        # Check for automation panel form fields
        idx = content.find('Pasos automatizados')
        if idx >= 0:
            print('Form section found')
            # Print surrounding context
            print(content[idx:idx+500])
else:
    print('No student user found')