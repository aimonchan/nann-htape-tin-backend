from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.db.models import Sum
# Restframework
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from datetime import datetime

# Others
import json
import random

# Custom Imports
from api import serializers as api_serializer
from api import models as api_models


# This code defines a DRF View class called MyTokenObtainPairView, which inherits from TokenObtainPairView.
class MyTokenObtainPairView(TokenObtainPairView):
    # Here, it specifies the serializer class to be used with this view.
    serializer_class = api_serializer.MyTokenObtainPairSerializer

# This code defines another DRF View class called RegisterView, which inherits from generics.CreateAPIView.
class RegisterView(generics.CreateAPIView):
    # It sets the queryset for this view to retrieve all User objects.
    queryset = api_models.User.objects.all()
    # It specifies that the view allows any user (no authentication required).
    permission_classes = (AllowAny,)
    # It sets the serializer class to be used with this view.
    serializer_class = api_serializer.RegisterSerializer


# This code defines another DRF View class called ProfileView, which inherits from generics.RetrieveAPIView and used to show user profile view.
class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = api_serializer.ProfileSerializer

    def get_object(self):
        user_id = self.kwargs['user_id']

        user = api_models.User.objects.get(id=user_id)
        profile = api_models.Profile.objects.get(user=user)
        return profile
    

def generate_numeric_otp(length=7):
        # Generate a random 7-digit OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
        return otp

class PasswordEmailVerify(generics.RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = api_serializer.UserSerializer
    
    def get_object(self):
        email = self.kwargs['email']
        user = api_models.User.objects.get(email=email)
        
        if user:
            user.otp = generate_numeric_otp()
            uidb64 = user.pk
            
             # Generate a token and include it in the reset link sent via email
            refresh = RefreshToken.for_user(user)
            reset_token = str(refresh.access_token)

            # Store the reset_token in the user model for later verification
            user.reset_token = reset_token
            user.save()

            link = f"http://localhost:5173/create-new-password?otp={user.otp}&uidb64={uidb64}&reset_token={reset_token}"
            
            merge_data = {
                'link': link, 
                'username': user.username, 
            }
            subject = f"Password Reset Request"
            text_body = render_to_string("email/password_reset.txt", merge_data)
            html_body = render_to_string("email/password_reset.html", merge_data)
            
            msg = EmailMultiAlternatives(
                subject=subject, from_email=settings.FROM_EMAIL,
                to=[user.email], body=text_body
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send()
        return user
    

class PasswordChangeView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = api_serializer.UserSerializer
    
    def create(self, request, *args, **kwargs):
        payload = request.data
        
        otp = payload['otp']
        uidb64 = payload['uidb64']
        password = payload['password']

        

        user = api_models.User.objects.get(id=uidb64, otp=otp)
        if user:
            user.set_password(password)
            user.otp = ""
            user.save()
            
            return Response( {"message": "Password Changed Successfully"}, status=status.HTTP_201_CREATED)
        else:
            return Response( {"message": "An Error Occured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateUserRoleView(APIView):
    def patch(self,request, user_id):
        try:
            user = api_models.User.objects.get(id=user_id)
        except api_models.User.DoesNotExist:
            return Response({'error':'User not found'},status=status.HTTP_404_NOT_FOUND)
        
        serializer = api_serializer.UserRoleUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#Active User
class ActiveUserListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.UserSerializer
    def get_queryset(self):
        return api_models.User.objects.filter(is_active_now=True)
######################## Post APIs ########################
        
# Product and SHop
class ProductListAPIView(generics.ListAPIView):
    queryset = api_models.Product.objects.all()
    serializer_class = api_serializer.ProductSerializer
    permission_classes = [AllowAny]
class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = api_models.Product.objects.all()
    serializer_class = api_serializer.ProductSerializer
    lookup_field = 'id'  # Same here, specifying to look up by 'id'

# Shop-List
class ShopListAPIView(generics.ListAPIView):
    queryset = api_models.Shop.objects.all()
    serializer_class = api_serializer.ShopSerializer
    permission_classes = [AllowAny]

# Shop-Detail
class ShopDetailAPIView(generics.RetrieveAPIView):
    queryset = api_models.Shop.objects.all()
    serializer_class = api_serializer.ShopSerializer
    lookup_field = 'id'  # By default, DRF looks for 'pk', but you can specify 'id' if you prefer.

# Order-create
class OrderCreateView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'order_maker': openapi.Schema(type=openapi.TYPE_INTEGER),
                'order_maker_money': openapi.Schema(type=openapi.TYPE_STRING),
                'is_active_now':openapi.Schema(type=openapi.TYPE_BOOLEAN)
            },
        ),
    )
    def post(self,request,*args,**kwargs):
        # Extract the necessary data from the request
        order_maker_money = request.data.get('order_maker_money')
        order_maker = request.data.get('order_maker')
        is_active_now = request.data.get('is_active_now')
        
        if not order_maker_money or not order_maker or not is_active_now:
            return Response({"detail": "Both 'order_maker_money and Order_maker is missing!'"}, status=status.HTTP_400_BAD_REQUEST)
        
        order_data= {
            'order_maker': order_maker,
            'order_maker_money':order_maker_money,
            'is_active_now':is_active_now
        }

        serializer = api_serializer.OrderSerializer(data=order_data)
        if serializer.is_valid():
            order = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#Order- List
class OrderListAPIView(generics.ListAPIView):
    queryset = api_models.Order.objects.all()
    serializer_class = api_serializer.OrderSerializer
    permission_classes=[AllowAny]
#Active Order
class ActiveOrderListAPIView(generics.ListAPIView):
    serializer_class= api_serializer.OrderSerializer
    def get_queryset(self):
        return api_models.Order.objects.filter(is_active_now=True)
    
#OrderItem - Create
class OrderItemCreateAPIView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'order': openapi.Schema(type=openapi.TYPE_INTEGER),
                'product_name': openapi.Schema(type=openapi.TYPE_STRING),
                'shop': openapi.Schema(type=openapi.TYPE_STRING),
                'purchaser': openapi.Schema(type=openapi.TYPE_INTEGER),
                'primary_amount': openapi.Schema(type=openapi.TYPE_STRING),
                'type': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )
    def post(self,request,*args,**kwargs):
        order =request.data.get('order')
        product_name = request.data.get('product_name')
        shop= request.data.get('shop')
        purchaser = request.data.get('purchaser')
        primary_amount=request.data.get('primary_amount')
        type=request.data.get('type')

        if not order:
            return Response({"detail": "Order is missing!'"}, status=status.HTTP_400_BAD_REQUEST)
        if not product_name:
            return Response({"detail": "Product is missing!'"}, status=status.HTTP_400_BAD_REQUEST)
        if not shop:
            return Response({"detail": "Shop is missing!'"}, status=status.HTTP_400_BAD_REQUEST)
        if not purchaser:
            return Response({"detail": "Purchaser is missing!'"}, status=status.HTTP_400_BAD_REQUEST)
        if not primary_amount:
            return Response({"detail": "Primary amount is missing!'"}, status=status.HTTP_400_BAD_REQUEST)
        if not type:
            return Response({"detail": "type is missing!'"}, status=status.HTTP_400_BAD_REQUEST)
        
        #Check if product already exists
        product = api_models.Product.objects.filter(name=product_name).first()
        if not product:
            #If product doesn't exist, create it
            product_serializer= api_serializer.ProductSerializer(data={'name':product_name})
            if product_serializer.is_valid():
                product = product_serializer.save() #Create the new product
            else:
                return Response(product_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        #Check if shop already exists
        shop = api_models.Shop.objects.filter(name=shop).first()
        if not shop: #just return a message but not create the instance as above
            return Response({'detail':'Shop Does not exist'},status=status.HTTP_400_BAD_REQUEST)
        
        #Check if purchaser a already existing User
        purchaser = api_models.User.objects.filter(username=purchaser).first()
        if not purchaser:
            return Response({'detail':'Purchaser Does not exist'},status=status.HTTP_400_BAD_REQUEST)

        
        oderitem_data= {
            'order':order,
            'product':product.id,
            'shop':shop.id,
            'purchaser':purchaser.id,
            'primary_amount':primary_amount,
            'type':type
        }
        serializer= api_serializer.OrderItemPostSerializer(data=oderitem_data)
        if serializer.is_valid():
            order = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

#OrderItem - Delete
class OrderItemDeleteAPIView(APIView):
    def delete(self, request, *args, **kwargs):
        order_item_id = kwargs.get('order_item_id')
        if not order_item_id:
            return Response({'detail':"Order item ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            order_item = api_models.OrderItem.objects.get(id=order_item_id)
        except api_models.OrderItem.DoesNotExist:
            return Response({'detail':"Order item not found!"}, status=status.HTTP_404_NOT_FOUND)
        order_item.delete()
        return Response({"detail":"Order item deleted successfully."},status=status.HTTP_204_NO_CONTENT)
    
#OrderItem- Edit
class OrderItemEditAPIView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'order': openapi.Schema(type=openapi.TYPE_INTEGER),
                'product': openapi.Schema(type=openapi.TYPE_STRING),
                'shop': openapi.Schema(type=openapi.TYPE_STRING),
                'purchaser': openapi.Schema(type=openapi.TYPE_INTEGER),
                'primary_amount': openapi.Schema(type=openapi.TYPE_STRING),
                'type': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )
    def put(self, request, *args, **kwargs):
        order_item_id = kwargs.get('order_item_id')
        try:
            order_item = api_models.OrderItem.objects.get(id=order_item_id)
        except api_models.OrderItem.DoesNotExist:
            return Response({'detail':"Order item not found!"}, status=status.HTTP_404_NOT_FOUND)
        order = request.data.get('order',order_item.order.id)
        product=request.data.get('product',order_item.product)
        shop = request.data.get('shop',order_item.shop)
        purchaser = request.data.get('purchaser',order_item.purchaser.id)
        primary_amount = request.data.get('primary_amount',order_item.primary_amount)
        type = request.data.get('type',order_item.type)

        orderitem_data={
            'order':order,
            'product':product,
            'shop':shop,
            'purchaser':purchaser,
            'primary_amount':primary_amount,
            'type':type
        }
        serializer= api_serializer.OrderItemSerializer(order_item,orderitem_data)
        if serializer.is_valid():
            order_item= serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#OrderItem- List
class OrderItemListAPIView(generics.ListAPIView):
    queryset = api_models.OrderItem.objects.all()
    serializer_class=api_serializer.OrderItemGetSerializer
    permission_classes=[AllowAny]

#SameShop OrderItem List
class SameShopOrderItemListAPIView(generics.ListAPIView):
    serializer_class = api_serializer.OrderItemGetSerializer
    def get(self,request,*args,**kwargs):
        #Get the active order (use .first()to get one active order)
        active_order = api_models.Order.objects.filter(is_active_now=True).first()
        if not active_order:
            return Response({'detail':'Active Order Not Found'}, status=status.HTTP_404_NOT_FOUND)
        sameorder_item = api_models.OrderItem.objects.filter(order=active_order)
        shopname = self.kwargs.get('shop') #Retrieve 'shop' from the URL
        shop= api_models.Shop.objects.filter(name=shopname).first()
        sameorder_item = sameorder_item.filter(shop_id=shop.id)

        serializer = self.serializer_class(sameorder_item,many=True)
        return Response(serializer.data)
        
#OrderItem-Detail
class OrderItemDetailAPIView(generics.RetrieveAPIView):
    queryset= api_models.OrderItem.objects.all()
    serializer_class=api_serializer.OrderItemGetSerializer
    lookup_field='id'

#Pending OrderItem List
class PendingOrderItemListAPIView(generics.ListAPIView):
    queryset = api_models.OrderItem.objects.filter(type='pending')
    serializer_class=api_serializer.OrderItemGetSerializer
    permission_classes=[AllowAny]
#In-Progress OrderItem List
class InProgressOrderItemListAPIView(generics.ListAPIView):
    queryset = api_models.OrderItem.objects.filter(type='in_progress')
    serializer_class=api_serializer.OrderItemGetSerializer
    permission_classes=[AllowAny]
#Complete OrderItem List
class CompleteOrderItemListAPIView(generics.ListAPIView):
    queryset = api_models.OrderItem.objects.filter(type='complete')
    serializer_class=api_serializer.OrderItemGetSerializer
    permission_classes=[AllowAny]



#MessageCreate in Order Item-Create
class MessageCreateInOrderItemView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'order_item': openapi.Schema(type=openapi.TYPE_INTEGER),
                'receiving_user': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER)),
                'sending_user': openapi.Schema(type=openapi.TYPE_INTEGER),
                'message': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
    )
    def post(self,request,*args,**kwargs):
        order_item=request.data.get('order_item')
        receiving_user=request.data.get('receiving_user',[])
        sending_user=request.data.get('sending_user')
        message=request.data.get('message')

        if not order_item:
            return Response({"detail": "order_item is missing!'"}, status=status.HTTP_400_BAD_REQUEST)
        if not receiving_user:
            return Response({"detail": "receiving_user is missing!'"}, status=status.HTTP_400_BAD_REQUEST)
        if not sending_user:
            return Response({"detail": "sending_user is missing!'"}, status=status.HTTP_400_BAD_REQUEST)
        if not message:
            return Response({"detail": "message is missing!'"}, status=status.HTTP_400_BAD_REQUEST)
        message_data={
            'order_item':order_item,
            'sending_user':sending_user,
            'message':message
        }
        serializer= api_serializer.OrderItemMessageSerializer(data=message_data)
        if serializer.is_valid():
            orderitemmessage= serializer.save()

            orderitemmessage.receiving_user.set(receiving_user)

            orderitemmessage.create_notification()
           
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
#Message List in Specific OrderItem
class MessageListInOrderItemView(generics.ListAPIView):
    serializer_class=api_serializer.OrderItemMessageSerializer
    permission_classes=[AllowAny]
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'order_item_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        ),
    )
    def get_queryset(self):
        order_item_id = self.kwargs.get('order_item_id')
        return api_models.OrderItemMessage.objects.filter(order_item=order_item_id)
    
#Mark Notification as Seen
class MarkNotificationAsSeenAPIView(APIView):
    def post(self,request,*args,**kwargs):
        order_item_id= request.data.get('order_item_id')
        user = request.user
        notifications= api_models.OrderItemMessageNotification.objects.filter(order_item=order_item_id,recipient=user,is_seen=False)

        if notifications.exists():
            notifications.update(is_seen=True)
        return Response({"detail":"Notifications marked as seen"},status=status.HTTP_200_OK)