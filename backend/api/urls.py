from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from api import views as api_views


urlpatterns = [
    # Userauths API Endpoints
    path('user/token/', api_views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('user/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/register/', api_views.RegisterView.as_view(), name='auth_register'),
    path('user/profile/<user_id>/', api_views.ProfileView.as_view(), name='user_profile'),
    path('user/password-reset/<email>/', api_views.PasswordEmailVerify.as_view(), name='password_reset'),
    path('user/password-change/', api_views.PasswordChangeView.as_view(), name='password_reset'),
    path('users/<int:user_id>/role/', api_views.UpdateUserRoleView.as_view(), name='update_user_role'),
    #Active User
    path('users/active-user-list/',api_views.ActiveUserListAPIView.as_view(),name='active-user-list'),

    # Shop Endpoints
    path('shops/', api_views.ShopListAPIView.as_view(), name='shop-list'),  # List all shops
    path('shops/<int:id>/', api_views.ShopDetailAPIView.as_view(), name='shop-detail'),  # Get a single shop by ID

    # Product Endpoints
    path('products/', api_views.ProductListAPIView.as_view(), name='product-list'),  # List all products
    path('products/<int:product_id>/', api_views.ProductDetailAPIView.as_view(), name='product-detail'),  # Get a single product by ID

    # Order Endpoints 
    path('orders/create/', api_views.OrderCreateView.as_view(), name='order-create'),
    #Order -List
    path('orders/list/',api_views.OrderListAPIView.as_view(),name='order-list'),

    # OrderItem Endpoints 
    path('orderitems/create/', api_views.OrderItemCreateAPIView.as_view(), name='orderitem-create'),
    path('orderitems/<int:order_item_id>/delete', api_views.OrderItemDeleteAPIView.as_view(), name='orderitem-delete'),
    path('orderitems/<int:order_item_id>/edit', api_views.OrderItemEditAPIView.as_view(), name='orderitem-edit'),
    path('orderitems/', api_views.OrderItemListAPIView.as_view(), name='orderitem-list'),
    path('orderitems/<int:id>/detail/', api_views.OrderItemDetailAPIView.as_view(), name='orderitem-detail'),
    #Same Shop Order Item List
    path('orderitems/<str:shop>/sameshop/',api_views.SameShopOrderItemListAPIView.as_view(),name='sameshop-orderitem-list'),


    #Pending Order Item List
    path('orderitems/pending/',api_views.PendingOrderItemListAPIView.as_view(),name="pending-orderitem_list"),
    #In-progress Order Item List
    path('orderitems/in-progoress/',api_views.InProgressOrderItemListAPIView.as_view(),name="inprogress-orderitem_list"),
    #Complete Order Item List
    path('orderitems/complete/',api_views.CompleteOrderItemListAPIView.as_view(),name="complete-orderitem_list"),

     #Active Order List
     path('orders/active-orders/',api_views.ActiveOrderListAPIView.as_view(),name='active_orders'),



    # OrderItem Message Endpoints 
    path('message/create/', api_views.MessageCreateInOrderItemView.as_view(), name='message-create'),

    # Message List in OrderItem  Endpoints 
    path('message/<int:order_item_id>/list/',api_views.MessageListInOrderItemView.as_view(),name="message-list-in-order-item"),

    # Mark Noti as Seen  Endpoints 
    path('notifications/mark_as_seen/',api_views.MarkNotificationAsSeenAPIView.as_view(),name="mark-notifications-seen")


]