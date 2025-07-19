from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializer import *
from django.contrib.auth import login
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
import random
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import *


class CreateAdminView(APIView):

    def post(self, request):
        serializer = AdminCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "Success": True,
                "message": "Admin created successfully!",
                "data": {
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                },
                "errors": None
            }, status=status.HTTP_201_CREATED)

        return Response({
            "Success": False,
            "message": "Validation failed.",
            "data": None,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AdminExistsView(APIView):
    def get(self, request):
        exists = CustomUser.objects.filter(is_superuser=True).exists()
        return Response({
            "Success": True,
            "message": "Checked successfully",
            "data": {"admin_exists": exists},
            "errors": None
        })


class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            Response_data = {
                "Success": True,
                "message": "User registered successfully.",
                "data": serializer.data,
                "errors": None
            }
            return Response(Response_data, status=status.HTTP_201_CREATED)

        Response_data = {
            "Success": False,
            "message": "Validation failed",
            "data": None,
            "errors": serializer.errors
        }
        return Response(Response_data, status=status.HTTP_400_BAD_REQUEST)


class AdminUserListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in [1, 2]:
            return Response({
                "Success": False,
                "message": "Unauthorized access",
                "data": None,
                "errors": "You are not authorized to view this page"
            }, status=status.HTTP_403_FORBIDDEN)

        users = CustomUser.objects.filter(role=3)
        serializer = UserRegistrationSerializer(users, many=True)
        return Response({
            "Success": True,
            "message": "User list fetched successfully",
            "data": serializer.data,
            "errors": None
        }, status=status.HTTP_200_OK)

    def delete(self, request, user_id=None):
        if request.user.role != 1:
            return Response({
                "Success": False,
                "message": "Unauthorized access",
                "data": None,
                "errors": "Only admins can delete users"
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            user = CustomUser.objects.get(id=user_id, role=3)
            user.delete()
            return Response({
                "Success": True,
                "message": "User deleted successfully.",
                "data": None,
                "errors": None
            }, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({
                "Success": False,
                "message": "User not found.",
                "data": None,
                "errors": "Invalid user ID"
            }, status=status.HTTP_404_NOT_FOUND)


class LoginView(APIView):

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(username=username, password=password)
            if user is None:
                return Response({
                    "Success": False,
                    "message": "Invalid credentials",
                    "errors": None
                }, status=status.HTTP_401_UNAUTHORIZED)

            token, _ = Token.objects.get_or_create(user=user)

            return Response({
                "Success": True,
                "message": "login successful",
                "token": token.key,
                "role": user.role,
                "errors": None
            }, status=status.HTTP_200_OK)

        return Response({
            "Success": False,
            "message": "Validation failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()  # Deletes the token from DB3
        return Response({
            "Success": True,
            "message": "Logged out successfully",
            "data": None,
            "errors": None
        })


class UserProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # request.user is a Python object ,React or any frontend cannot understand Python objects,So we pass the user into the serializer, and it converts it into serializable data — usually a dictionary (dict) that can be converted to JSON.
        serializer = UserRegistrationSerializer(user)
        Response_data = {
            "Success": True,
            "message": "User profile fetched successfully.",
            "data": serializer.data,
            "errors": None
        }
        return Response(Response_data, status=status.HTTP_200_OK)


class UserProfileUpdateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = UserProfileUpdateSerializer(
            user, data=request.data, partial=True,  context={'request': request})
        if serializer.is_valid():
            serializer.save()
            Response_data = {
                "Success": True,
                "message": "Profile updated successfully",
                "data": serializer.data,
                "errors": None
            }
            return Response(Response_data, status=status.HTTP_200_OK)
        Response_data = {
            "Success": False,
            "message": "Update failed",
            "data": None,
            "errors": serializer.errors
        }

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffRegistrationView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 1:
            return Response({"error": "Only admins can create staff users."}, status=status.HTTP_403_FORBIDDEN)

        serializer = StaffRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "Success": True,
                "message": "Staff user created successfully.",
                "data": serializer.data,
                "errors": None
            }, status=status.HTTP_201_CREATED)

        return Response({
            "Success": False,
            "message": "Validation failed",
            "data": None,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        if request.user.role != 1:
            return Response({"error": "Only admins can create staff users."}, status=status.HTTP_403_FORBIDDEN)

        users = CustomUser.objects.filter(role=2)
        serializer = StaffRegistrationSerializer(users, many=True)
        return Response({
            "Success": True,
            "message": "Staff users fetched successfully.",
            "data": serializer.data,
            "errors": None
        }, status=status.HTTP_200_OK)

    def delete(self, request, staff_id):
        if request.user.role != 1:
            return Response({"error": "Only admins can create staff users."}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = CustomUser.objects.get(id=staff_id, role=2)
            user.delete()
            return Response({
                "Success": True,
                "message": "Staff user deleted successfully.",
                "data": None,
                "errors": None
            }, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({
                "Success": False,
                "message": "Staff user not found.",
                "data": None,
                "errors": "Invalid staff ID"
            }, status=status.HTTP_404_NOT_FOUND)


class StaffProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = StaffRegistrationSerializer(user)
        Response_data = {
            "Success": True,
            "message": "User profile fetched successfully.",
            "data": serializer.data,
            "errors": None
        }
        return Response(Response_data, status=status.HTTP_200_OK)


class StaffProfileUpdateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = StaffProfileUpdateSerializer(
            user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            Response_data = {
                "Success": True,
                "message": "Profile updated successfully.",
                "data": serializer.data,
                "errors": None
            }
            return Response(Response_data, status=status.HTTP_200_OK)

        Response_data = {
            "Success": False,
            "message": "Validation failed",
            "data": None,
            "errors": serializer.errors
        }
        return Response(Response_data, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            Response_data = {
                "Success": True,
                "message": "Password changed successfully.",
                "data": None,
                "errors": None
            }
            return Response(Response_data, status=status.HTTP_200_OK)

        Response_data = {
            "Success": False,
            "message": "Password change failed.",
            "data": None,
            "errors": serializer.errors
        }
        return Response(Response_data, status=status.HTTP_400_BAD_REQUEST)


class RequestOtpView(APIView):
    def post(self, request):
        serializer = RequestOtpSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            try:
                user = CustomUser.objects.get(username=username)
            except CustomUser.DoesNotExist:
                return Response({
                    "Success": False,
                    "message": "User not found",
                }, status=404)

            otp = str(random.randint(100000, 999999))
            PasswordResetOtp.objects.create(user=user, otp=otp)

            send_mail(
                subject='Your Password Reset OTP',
                message=f'Hello {user.username}, your OTP for password reset is {otp}. It is valid for 2 minutes.',
                from_email='athulkp129@gmail.com',
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response({
                "Success": True,
                "message": "OTP sent to email",
                "data": None,
                "errors": None
            })
        return Response({
            "Success": False,
            "message": "Validation failed",
            "data": None,
            "errors": serializer.errors
        }, status=400)


class VerifyOtpView(APIView):
    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            otp = serializer.validated_data['otp']
            try:
                user = CustomUser.objects.get(username=username)
                otp_instance = PasswordResetOtp.objects.filter(
                    user=user, otp=otp).latest("created_at")

                if otp_instance.is_expired():
                    return Response({
                        "Success": False,
                        "message": "OTP expired",
                    }, status=400)

                otp_instance.is_verified = True
                otp_instance.save()

                return Response({
                    "Success": True,
                    "message": "OTP verified",
                })

            except (CustomUser.DoesNotExist, PasswordResetOtp.DoesNotExist):
                return Response({
                    "Success": False,
                    "message": "Invalid username or OTP",
                    "data": None,
                    "errors": None
                }, status=400)

        return Response({
            "Success": False,
            "message": "Validation failed",
            "data": None,
            "errors": serializer.errors
        }, status=400)


class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            new_password = serializer.validated_data['new_password']
            try:
                user = CustomUser.objects.get(username=username)
                otp_instance = PasswordResetOtp.objects.filter(
                    user=user).latest("created_at")

                if not otp_instance.is_verified:
                    return Response({
                        "Success": False,
                        "message": "OTP not verified",
                    }, status=400)

                user.set_password(new_password)
                user.save()

                otp_instance.delete()

                return Response({
                    "Success": True,
                    "message": "Password reset successful",
                    "data": None,
                    "errors": None
                })

            except (CustomUser.DoesNotExist, PasswordResetOtp.DoesNotExist):
                return Response({
                    "Success": False,
                    "message": "User not found or no OTP record",
                }, status=400)

        return Response({
            "Success": False,
            "message": "Validation failed",
            "data": None,
            "errors": serializer.errors
        }, status=400)


class FacilityCreateView(APIView):
    def post(self, request):
        data = request.data
        serializer = FacilitySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Facilities created", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FacilityListAPIView(APIView):
    def get(self, request):
        facilities = Facility.objects.all()
        serializer = FacilitySerializer(facilities, many=True)
        return Response({
            "Success": True,
            "message": "Facilities fetched successfully",
            "data": serializer.data,
            "errors": None
        })


class RoomAPIView(APIView):
    def post(self, request):
        serializer = RoomSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            room = serializer.save()
            serializer = RoomSerializer(room, context={'request': request})
            return Response({
                "Success": True,
                "message": "Room created successfully",
                "data": serializer.data,
                "errors": None
            }, status=status.HTTP_201_CREATED)
        return Response({
            "Success": False,
            "message": "Validation failed",
            "data": None,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, id=None):
        if id:
            try:
                room = Room.objects.get(id=id)
                serializer = RoomSerializer(room, context={'request': request})
                return Response(serializer.data)
            except Room.DoesNotExist:
                return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            rooms = Room.objects.all()
            serializer = RoomSerializer(
                rooms, many=True, context={'request': request})
            return Response(serializer.data)

    def put(self, request, id=None):
        if not id:
            return Response({"error": "Room ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        room = get_object_or_404(Room, id=id)
        serializer = RoomSerializer(
            room, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            room = serializer.save()
            serializer = RoomSerializer(room, context={'request': request})
            return Response({
                "Success": True,
                "message": "Room updated successfully",
                "data": serializer.data,
                "errors": None
            }, status=status.HTTP_200_OK)
        return Response({
            "Success": False,
            "message": "Update failed",
            "data": None,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        if not id:
            return Response({"error": "Room ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        room = get_object_or_404(Room, id=id)
        room.delete()
        return Response({"message": "Room deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class BookedDatesView(APIView):
    def get(self, request, room_id):
        bookings = Booking.objects.filter(
            room_id=room_id,
            is_approved=True
        ).values("check_in", "check_out")  # Directly gives you what you need

        return Response({
            "Success": True,
            "message": "Booked dates fetched successfully.",
            # already dicts, no serializer or loop needed
            "data": list(bookings)
        }, status=status.HTTP_200_OK)


class CreateBookingView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BookingSerializer(
            data=request.data)

        if serializer.is_valid():
            room = serializer.validated_data['room']
            check_in = serializer.validated_data['check_in']
            check_out = serializer.validated_data['check_out']
            num_days = (check_out - check_in).days
            total_price = room.price * num_days

            booking = Booking.objects.create(
                user=request.user,
                room=room,
                check_in=check_in,
                check_out=check_out,
                total_price=total_price
            )

            admin_user = CustomUser.objects.get(role=1)
            if admin_user:
                Notification.objects.create(
                    user=admin_user,
                    message=f"New booking request from {request.user.username} for room '{room.name}' from {check_in} to {check_out}.",
                )

            response_data = BookingSerializer(booking).data
            return Response({
                "Success": True,
                "message": "Booking request sent.",
                "data": response_data,
                "errors": None
            }, status=status.HTTP_201_CREATED)

        return Response({
            "Success": False,
            "message": "Booking failed.",
            "data": None,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class BookingRequestListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 1:  # assuming role=1 is admin
            return Response({"detail": "Not authorized"}, status=403)

        pending_bookings = Booking.objects.filter(
            is_approved=False, is_rejected=False)
        serializer = PendingBookingSerializer(pending_bookings, many=True)
        return Response({
            "Success": True,
            "message": "Pending booking requests fetched.",
            "data": serializer.data,
            "errors": None
        })


class ApproveRejectBookingView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        if request.user.role != 1:
            return Response({"detail": "Not authorized"}, status=403)

        action = request.data.get("action")  # "approve" or "reject"

        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found"}, status=404)

        if action == "approve":
            booking.is_approved = True
            booking.save()

            # ✅ Send approval email
            send_mail(
                subject="Your Room Booking Has Been Approved",
                message=(
                    f"Hi {booking.user.username},\n\n"
                    f"Good news! Your booking for room '{booking.room.name}' "
                    f"from {booking.check_in} to {booking.check_out} has been approved.\n\n"
                    "We look forward to hosting you!"
                ),
                from_email='athulkp129@gmail.com',
                recipient_list=[booking.user.email],
                fail_silently=False,
            )

            Notification.objects.create(
                user=booking.user,
                message=f"Your booking for room '{booking.room.name}' has been approved.",
            )

            message = "Booking approved."

        elif action == "reject":
            booking.is_rejected = True
            booking.is_approved = False
            booking.save()

            # ✅ Send rejection email
            send_mail(
                subject="Your Room Booking Has Been Rejected",
                message=(
                    f"Hi {booking.user.username},\n\n"
                    f"We're sorry to inform you that your booking for room '{booking.room.name}' "
                    f"from {booking.check_in} to {booking.check_out} has been rejected.\n\n"
                    "Please try booking a different date or room."
                ),
                from_email='athulkp129@gmail.com',
                recipient_list=[booking.user.email],
                fail_silently=False,
            )

            Notification.objects.create(
                user=booking.user,
                message=f"Your booking for room '{booking.room.name}' has been rejected.",
            )

            message = "Booking rejected."

        else:
            return Response({"detail": "Invalid action"}, status=400)

        return Response({
            "Success": True,
            "message": message,
            "data": BookingSerializer(booking).data,
            "errors": None
        })

# user booking list view


class UserBookingListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.filter(
            user=request.user).order_by('-check_in')
        serializer = UserBookingSerializer(bookings, many=True)
        return Response({
            "Success": True,
            "message": "Your bookings retrieved.",
            "data": serializer.data,
            "errors": None
        })


class CancelBookingView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id, user=request.user)

            if booking.is_approved or booking.is_rejected:
                return Response({
                    "Success": False,
                    "message": "Cannot cancel a booking that is already approved or rejected.",
                    "data": None,
                    "errors": None
                }, status=400)

            admin_user = CustomUser.objects.get(role=1)
            if admin_user:
                Notification.objects.create(
                    user=admin_user,
                    message=f"{request.user.username} canceled their booking for room ."
                )

            booking.delete()

            return Response({
                "Success": True,
                "message": "Booking cancelled successfully.",
                "data": None,
                "errors": None
            })

        except Booking.DoesNotExist:
            return Response({
                "Success": False,
                "message": "Booking not found.",
                "data": None,
                "errors": None
            }, status=404)


class ApprovedBookingListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        approved_bookings = Booking.objects.filter(
            is_approved=True, is_rejected=False)
        serializer = ApprovedBookingSerializer(approved_bookings, many=True)
        return Response({"Success": True, "data": serializer.data}, status=status.HTTP_200_OK)


class RejectedBookingListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rejected_bookings = Booking.objects.filter(
            is_approved=False, is_rejected=True)
        serializer = RejectedBookingSerializer(rejected_bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeleteBookingView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found."}, status=404)

        booking.delete()
        return Response({"message": "Booking deleted successfully."}, status=200)

# filtering rooms based on status for staff room booking


class RoomListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rooms = Room.objects.filter(status='available')
        serializer = RoomListSerializer(rooms, many=True)
        return Response({
            "Success": True,
            "message": "Room list fetched successfully",
            "data": serializer.data,
            "errors": None
        })



class StaffBookingForUserView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 2:
            return Response({
                "Success": False,
                "message": "Only staff can book rooms for users.",
            }, status=403)

        data = request.data
        user_id = data.get('user_id')

        if not user_id:
            return Response({
                "Success": False,
                "message": "User ID is required.",
            }, status=400)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                "Success": False,
                "message": "User not found.",
            }, status=404)

        serializer = BookingSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            room = serializer.validated_data['room']
            check_in = serializer.validated_data['check_in']
            check_out = serializer.validated_data['check_out']

            num_days = (check_out - check_in).days
            total_price = room.price * num_days

            booking = Booking.objects.create(
                user=user,
                room=room,
                check_in=check_in,
                check_out=check_out,
                total_price=total_price,
                booked_by=request.user  # ✅ This line is new
            )

            # Notify admin about the booking
            admin_user = CustomUser.objects.get(role=1)
            if admin_user:
                Notification.objects.create(
                    user=admin_user,
                    message=f"New booking request from '{request.user.username}' for user '{user.username}' for room '{room.name}' from {check_in} to {check_out}.",
                )

            response_data = BookingSerializer(booking).data
            return Response({
                "Success": True,
                "message": "Room booked successfully for user.",
                "data": response_data,
                "errors": None
            }, status=201)

        return Response({
            "Success": False,
            "message": "Booking validation failed.",
            "data": None,
            "errors": serializer.errors
        }, status=400)


class StaffBookingListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        staff_user = request.user
        bookings = Booking.objects.filter(booked_by=staff_user).order_by('-check_in')
        serializer = StaffBookingSerializer(bookings, many=True)
        return Response({
            "Success": True,
            "message": "Bookings made by you (staff) retrieved.",
            "data": serializer.data,
            "errors": None
        })

class NotificationListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            notifications = Notification.objects.filter(
                user=request.user).order_by('-created_at')
            serializer = NotificationSerializer(notifications, many=True)
            return Response({
                "Success": True,
                "message": "Notifications fetched successfully.",
                "data": serializer.data,
                "errors": None
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "Success": False,
                "message": "Failed to fetch notifications.",
                "data": None,
                "errors": serializer.errors
            }, status=status.HTTP_204_NO_CONTENT)


class UnreadNotificationCountView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            user=request.user, is_read=False).count()
        return Response({
            "Success": True,
            "message": "Unread count fetched successfully.",
            "data": {"count": count},
            "errors": None
        })


class MarkNotificationsAsReadView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(
            user=request.user, is_read=False).update(is_read=True)
        return Response({
            "Success": True,
            "message": "Notifications marked as read.",
            "data": None,
            "errors": None
        })


class SubmitComplaintView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        serializer = ComplaintSerializer(
            data=request.data, context={'request': request})

        if serializer.is_valid():
            complaint = serializer.save()

            try:

                admin_user = CustomUser.objects.get(role=1)
                Notification.objects.create(
                    user=admin_user,
                    message=f"New complaint submitted by {request.user.username}",
                )
            except CustomUser.DoesNotExist:
                pass

            return Response({
                "Success": True,
                "message": "Complaint submitted successfully.",
                "data": ComplaintSerializer(complaint).data,
                "errors": None
            }, status=status.HTTP_201_CREATED)

        return Response({
            "Success": False,
            "message": "Failed to submit complaint.",
            "data": None,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class AdminComplaintListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        if request.user.role != 1:  # only admin
            return Response({
                "Success": False,
                "message": "Permission denied.",
                "data": None,
                "errors": None
            }, status=403)

        complaints = Complaint.objects.all().order_by('-created_at')
        serializer = ComplaintSerializer(complaints, many=True)
        return Response({
            "Success": True,
            "message": "Complaints fetched.",
            "data": serializer.data,
            "errors": None
        })


class MarkComplaintResolvedView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request, complaint_id):
        if request.user.role != 1:
            return Response({
                "Success": False,
                "message": "Permission denied.",
                "data": None,
                "errors": None
            }, status=403)

        try:
            complaint = Complaint.objects.get(id=complaint_id)
        except Complaint.DoesNotExist:
            return Response({
                "Success": False,
                "message": "Complaint not found.",
                "data": None,
                "errors": None
            }, status=404)

        complaint.is_resolved = True
        complaint.save()

        return Response({
            "Success": True,
            "message": "Complaint marked as resolved.",
            "data": ComplaintSerializer(complaint).data,
            "errors": None
        })


class AdminMessage(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        if request.user.role != 1:
            return Response({
                "Success": False,
                "message": "Only admin can send messages.",
                "data": None,
                "errors": None
            }, status=403)

        message = request.data.get('message')
        target = request.data.get('target')  # 'staff' or 'users'

        if not message or not target:
            return Response({
                "Success": False,
                "message": "Message and target are required.",
                "data": None,
                "errors": None
            }, status=400)

        if target == 'staff':
            recipients = CustomUser.objects.filter(role=2)
        elif target == 'users':
            recipients = CustomUser.objects.filter(role=3)
        else:
            return Response({
                "Success": False,
                "message": "Invalid target. Use 'staff' or 'users'.",
                "data": None,
                "errors": None
            }, status=400)

        for user in recipients:
            Notification.objects.create(user=user, message=message)

        return Response({
            "Success": True,
            "message": f"Message sent to all {target}.",
            "data": None,
            "errors": None
        }, status=201)
