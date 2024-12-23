from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
# from shortuuid.django_fields import ShortUUIDField
# import shortuuid

# User model
class User(AbstractUser):
    ROLES = (
    ('Normal User', 'Normal User'),
    ('Shop Owner', 'Shop Owner'),
    ('Order Maker', 'Order Maker'),
    ('Purchaser', 'Purchaser'),
)
    username = models.CharField(unique=True, max_length=100)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    role = models.CharField(choices=ROLES, max_length=100, default="Normal User")  # Add role field here
    is_active_now = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    
    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        email_username, email_domain = self.email.split('@')
        if self.full_name == "" or self.full_name is None:
            self.full_name = email_username
        if self.username == "" or self.username is None:
            self.username = email_username
        super(User, self).save(*args, **kwargs)


# Profile model
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.FileField(upload_to="image", default="default/default-user.jpg", null=True, blank=True)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    bio = models.CharField(max_length=100, null=True, blank=True)
    about = models.CharField(max_length=100, null=True, blank=True)
    author = models.BooleanField(default=False)
    country = models.CharField(max_length=100, null=True, blank=True)
    facebook = models.CharField(max_length=100, null=True, blank=True)
    twitter = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        if self.full_name == "" or self.full_name is None:
            self.full_name = self.user.full_name
        super(Profile, self).save(*args, **kwargs)


# Signal handler to automatically create a profile when a user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# Signal handler to save the profile whenever the user is saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=255, null=True,blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True,blank=True)

    def __str__(self):
        return self.name

class Shop(models.Model):
    name = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=15)
    available_items = models.ManyToManyField(Product, related_name='shops', blank=True)
    address = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    map_url = models.URLField(null=True, blank=True)
    bg_color = models.CharField(max_length=255, null=True, blank=True)
    text_color = models.CharField(max_length=255,null=True,blank=True)

    def __str__(self):
        return self.name
    
class Order(models.Model):
    order_code = models.CharField(max_length=50, unique=True) 
    order_maker_money = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  
    purchaser_money = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  
    date_added = models.DateTimeField(auto_now_add=True)  
    taxi_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Taxi fee amount
    is_complete = models.BooleanField(default=False)
    is_active_now = models.BooleanField(default=False)
    order_maker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders",null=True, blank=True)

    def generate_order_code(self): # The format will be: DD-MM-YYYY-ordermaker-username-purchaser-username
        # Format the date as DD-MM-YYYY
        date_stamp = timezone.now().strftime('%d-%m-%Y')  # Current date 
        return f"{date_stamp}"

    def save(self, *args, **kwargs):
        """
        Override save method to automatically generate order_code before saving the instance.
        """
        if not self.order_code:
            self.order_code = self.generate_order_code()  # Set the order_code only if it's not already set
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_code} - Complete: {self.is_complete}"

    class Meta:
        ordering = ['date_added']


class OrderPurchaser(models.Model):
    order = models.ForeignKey(Order, null=True,blank=True,related_name="purchaser", on_delete=models.CASCADE)
    purchaser = models.OneToOneField(User, null=True, blank=True, related_name='orderpurchaser_purchaser', on_delete=models.CASCADE)
    purchaser_money = models.DecimalField(max_digits=10, decimal_places=2, null=True,blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
   
    def __str__(self):
        return f"OrderPurchaser for {self.purchaser.username} - {self.order.order_code}"
      
class OrderItem(models.Model):
    UNIT_CHOICES= (
        ('KyatThar', 'KyatThar'),
        ('PeikThar', 'PeikThar'),
        ('PaLinn', 'PaLinn'),
        ('Htope', 'Htope'),
        ('Tone', 'Tone'),
        ('Khu', 'Khu'),
    )
    TYPE_CHOICES = (
        ('pending', 'pending'),
        ('in_progress', 'in_progress'),
        ('complete', 'complete'),
    )

    order = models.ForeignKey(Order, null= True,blank=True, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, null=True, blank=True, related_name='order_items', on_delete=models.CASCADE)
    shop= models.ForeignKey(Shop, null=True,blank=True, related_name="items_shops", on_delete=models.SET_NULL)
    purchaser = models.ForeignKey(User, null=True,blank=True, related_name="orderitem", on_delete=models.CASCADE)
    # ordermaker= models.ForeignKey(OrderMaker, null=True,blank=True, related_name="orderitem", on_delete=models.SET_NULL)
    primary_amount = models.CharField(max_length=50, null=True,blank=True) 
    type = models.CharField(choices=TYPE_CHOICES, max_length=100, default="pending")
    date_added = models.DateTimeField(auto_now_add=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unread_users = models.ManyToManyField(OrderPurchaser, related_name='unread_users', blank=True)

    def __str__(self):
        return f"OrderItem {self.id} - {self.product.name}"
    
class OrderItemMessage(models.Model):
    order_item = models.ForeignKey(OrderItem, null=True, blank=True, related_name='messages', on_delete=models.CASCADE)
    receiving_user = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='received_messages')
    sending_user = models.OneToOneField(settings.AUTH_USER_MODEL, blank=True,null=True, related_name='sent_messages',on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    seen_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='seen_messages')
    message=models.TextField(blank=True,null=True, max_length=200)

    def __str__(self):
        return f"Message from {self.sending_user} in {self.order_item.order.order_code}"
    def create_notification(self):
        """Automatically create a notification when a new message is created"""
        for user in self.receiving_user.all():
            notification = OrderItemMessageNotification.objects.create(
                order_item=self.order_item,
                recipient= user,
                message=self.message,
                is_seen=False
            )

    def save(self,*args,**kwargs): #save the message first
        super().save(*args,**kwargs)
        self.create_notification()

class OrderItemMessageNotification(models.Model):
    order_item = models.ForeignKey(OrderItem, null=True, blank=True, related_name='notifications', on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True,null=True, related_name='received_notifications',on_delete=models.CASCADE)
    message = models.TextField(max_length=200, null=True, blank=True)
    is_seen = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Notification for {self.recipient}"