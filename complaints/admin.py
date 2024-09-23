from django.contrib import admin
from .models import Complaint, Responsible

admin.site.register(Complaint)
admin.site.register(Responsible)