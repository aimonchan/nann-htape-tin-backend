from django.contrib import admin
from api import models as api_models

# Register your models here.
admin.site.register(api_models.User)
admin.site.register(api_models.Profile)

# For Nann Htape Tin
admin.site.register(api_models.Product)
admin.site.register(api_models.Shop)
admin.site.register(api_models.Order)
admin.site.register(api_models.OrderPurchaser)
admin.site.register(api_models.OrderItem)
admin.site.register(api_models.OrderItemMessage)
admin.site.register(api_models.OrderItemMessageNotification)