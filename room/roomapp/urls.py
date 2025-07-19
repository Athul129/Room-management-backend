from django.urls import path
from .views import*
urlpatterns=[
    
    #url for  admin

    path('create-admin/', CreateAdminView.as_view()),
    path("check-admin/", AdminExistsView.as_view()),


    #login logout
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    #url for registerations staff user

    path('register/', UserRegistrationView.as_view(), name='register'),
    path('staff_create/', StaffRegistrationView.as_view()),

    #listing of users(2,3)
    path('admin/users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('admin/users/<int:user_id>/', AdminUserListView.as_view(), name='admin-user-delete'),
    path('staff_create/<int:staff_id>/', StaffRegistrationView.as_view()),


    #profiles

    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile_update/', UserProfileUpdateView.as_view(), name='profile-update'),

    path('profile-staff/', StaffProfileView.as_view()),
    path('staff_profile_update/', StaffProfileUpdateView.as_view(), name='staff_profile_update'),



    #password change and reset
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),    
    path('request-otp/', RequestOtpView.as_view(), name='request-otp'),
    path('verify-otp/', VerifyOtpView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),


    path('facility_create/', FacilityCreateView.as_view(), name='facility-create'),
    path('facilities/', FacilityListAPIView.as_view()),
    path('rooms/', RoomAPIView.as_view(), name='rooms'),             # For POST and GET (list)
    path('rooms/<int:id>/', RoomAPIView.as_view()),

    
    #room booking
    path('room-booking/', CreateBookingView.as_view()),
    
    path("rooms/<int:room_id>/booked-dates/", BookedDatesView.as_view(), name="room-booked-dates"),
    path('booking-requests/',BookingRequestListView .as_view()),
    path("booking-action/<int:booking_id>/", ApproveRejectBookingView.as_view(), name="booking-action"),


    path("my-bookings/", UserBookingListView.as_view(), name="user-bookings"),
    path("cancel-booking/<int:booking_id>/", CancelBookingView.as_view(), name="cancel-booking"),

    
    path('approved-bookings/', ApprovedBookingListView.as_view(), name='approved-bookings'),
    path('rejected-bookings/', RejectedBookingListView.as_view(), name='rejected-bookings'),
    path('deletebookings/<int:booking_id>/', DeleteBookingView.as_view()),


    path('staff/book-room/', StaffBookingForUserView.as_view()),
    path('staff/bookings/', StaffBookingListView.as_view(), name='staff-booking-list'),
    path('roomstaff/', RoomListView.as_view(),),


    #notifications
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path("notifications/unread-count/", UnreadNotificationCountView.as_view(), name="unread-count"),
    path("notifications/mark-read/", MarkNotificationsAsReadView.as_view(), name="mark-as-read"),
    
    path("admin/message/", AdminMessage.as_view(),),


    #complaints
    path('complaints/submit/', SubmitComplaintView.as_view()),
    path('admin/complaints/', AdminComplaintListView.as_view()),
    path('admin/complaints/<int:complaint_id>/resolve/', MarkComplaintResolvedView.as_view()),

]

