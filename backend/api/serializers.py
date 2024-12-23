from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from api import models as api_models
from django.conf import settings
# from django.contrib.auth.models import User

# User = settings.AUTH_USER_MODEL
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['full_name'] = user.full_name
        token['email'] = user.email
        token['username'] = user.username
        try:
            token['vendor_id'] = user.vendor.id
        except:
            token['vendor_id'] = 0

         # Add the role (from either User or Profile model)
        try:
            token['role'] = user.profile.role  # Assuming 'role' is stored in the Profile model
        except:
            token['role'] = 'Normal User'  # Default role if no profile or role is set
        return token
    
class RegisterSerializer(serializers.ModelSerializer):
    # Define fields for the serializer, including password and password2
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        # Specify the model that this serializer is associated with
        model = api_models.User
        # Define the fields from the model that should be included in the serializer
        fields = ('full_name', 'email',  'password', 'password2')

    def validate(self, attrs):
        # Define a validation method to check if the passwords match
        if attrs['password'] != attrs['password2']:
            # Raise a validation error if the passwords don't match
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # Return the validated attributes
        return attrs

    def create(self, validated_data):
        # Define a method to create a new user based on validated data
        user = api_models.User.objects.create(
            full_name=validated_data['full_name'],
            email=validated_data['email'],
        )
        email_username, mobile = user.email.split('@')
        user.username = email_username

        # Set the user's password based on the validated data
        user.set_password(validated_data['password'])
        user.save()
        # Return the created user
        return user
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.User
        fields = '__all__'

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Profile
        fields = '__all__'
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['user']= UserSerializer(instance.user).data
        return response
    
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.User
        fields = ['role']
         # Optionally, add any validation if needed, for example, ensuring only valid roles are set
        extra_kwargs = {
            'role': {'required': True}
        }

##.......................................................................................................................................................................

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Product
        fields = ['id', 'name', 'description', 'price']

class ShopSerializer(serializers.ModelSerializer):
    # Include the related products in the Shop Serializer
    available_items = ProductSerializer(many=True, read_only=True)  # Nested serializer for available products

    class Meta:
        model = api_models.Shop
        fields = ['id', 'name', 'contact_number', 'address', 'latitude', 'longitude', 'map_url', 'available_items','bg_color','text_color']
#........................................................................................................................................................................
#OrderItem Get Serializer (for OrderItemCreateAPIView)
class OrderItemGetSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    shop = ShopSerializer()
    purchaser = UserSerializer()
    order = serializers.PrimaryKeyRelatedField(queryset=api_models.Order.objects.all(),required=False)
    type= serializers.ChoiceField(choices=api_models.OrderItem.TYPE_CHOICES, required=False)
    class Meta:
        model= api_models.OrderItem
        fields = fields = [
            'id', 'order', 'product', 'shop','purchaser', 'primary_amount','unread_users','type'
        ]


    
# OrderItem Post Serializer (for OrderItemCreateAPIView)
class OrderItemPostSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=api_models.Shop.objects.all(),required=False)
    purchaser = serializers.PrimaryKeyRelatedField(queryset=api_models.User.objects.all(),required=False)
    product = serializers.PrimaryKeyRelatedField(queryset=api_models.Product.objects.all(),required=False)
    order = serializers.PrimaryKeyRelatedField(queryset=api_models.Order.objects.all(),required=False)
    type= serializers.ChoiceField(choices=api_models.OrderItem.TYPE_CHOICES, required=False)

    class Meta:
        model=api_models.OrderItem
        fields = fields = [
            'id', 'order', 'product', 'shop','purchaser', 'primary_amount','unread_users','type'
        ]
        extra_kwargs={
            'type':{'required':False}# Ensure the `type` is optional for update operations
        }

    def create(self, validated_data):
        order = validated_data.get('order')
        product = validated_data.get('product')
        shop = validated_data.get('shop')
        purchaser = validated_data.get('purchaser')
        primary_amount= validated_data.get('primary_amount')
        type=validated_data.get('type')

        orderitem = api_models.OrderItem.objects.create(
            order=order,
            product=product,
            shop=shop,
            purchaser=purchaser,
            primary_amount=primary_amount,
            type=type
           
        )
        return orderitem
    
#OrderItemMessage Serializer
class OrderItemMessageSerializer(serializers.ModelSerializer):
    order_item=serializers.PrimaryKeyRelatedField(queryset=api_models.OrderItem.objects.all(),required=False)
    receiving_user=serializers.PrimaryKeyRelatedField(queryset=api_models.User.objects.all(),required=False, many=True)
    sending_user=serializers.PrimaryKeyRelatedField(queryset=api_models.User.objects.all(),required=False)
    
    class Meta:
        model =api_models.OrderItemMessage
        fields = '__all__'

    def create(self,validated_data):
        order_item= validated_data.get('order_item')
        receiving_user= validated_data.get('receiving_user',[])
        sending_user= validated_data.get('sending_user',[])
        message = validated_data.get('message')

        orderitem_message= api_models.OrderItemMessage.objects.create(
            order_item=order_item,
            sending_user=sending_user,
            message=message
        )
         # Use .set() method to assign many-to-many relationships after object creation
        if receiving_user:
            orderitem_message.receiving_user.set(receiving_user)

        return orderitem_message

# Order Serializer
class OrderSerializer(serializers.ModelSerializer):
    items= OrderItemGetSerializer(many=True,read_only=True)
    # items = serializers.PrimaryKeyRelatedField(queryset=api_models.OrderItem.objects.all(),required=False, many=True)
    order_maker= UserSerializer(read_only=True)
    # order_maker = serializers.PrimaryKeyRelatedField(queryset=api_models.User.objects.all(),required=False)
    # active_orders= serializers.SerializerMethodField()

    class Meta:
        model = api_models.Order
        fields = [
            'id', 'order_code', 'order_maker_money', 'purchaser_money','date_added', 'taxi_fee','is_complete','order_maker','is_active_now','items'
        ]
        read_only_fields = ['order_code', 'date_added', 'is_complete'] 
         # `order_code` and `date_added` are auto-generated
        

    def __init__(self, *args, **kwargs):
        super(OrderSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'POST':
            self.Meta.depth = 0
        else:
            self.Meta.depth = 1

    def create(self, validated_data):
         order_maker_money = validated_data.get('order_maker_money')
         order_maker = validated_data.get('order_maker')
         is_active_now= validated_data.get('is_active_now')
         # Create the order object
         order= api_models.Order.objects.create(
             order_maker_money=order_maker_money,
             order_maker=order_maker,
             is_active_now=is_active_now
         )
         return order
    
    # def get_active_orders(self, obj):
    #     active_orders = api_models.Order.objects.filter(is_active_now=True)
    #     print(active_orders)  # Add this to debug
    #     return OrderSerializer(active_orders, many=True, context={'request': self.context['request']}).data

