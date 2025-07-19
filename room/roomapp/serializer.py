from rest_framework import serializers
from .models import*


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)  #: Ensures password is used only for input, not shown in responses.

    class Meta:
        model = CustomUser
        fields = [ 'id',   'username', 'email', 'phonenumber', 'address', 'password']

    def create(self, validated_data):
        validated_data['role'] = 3 
        return CustomUser.objects.create_user(**validated_data)


    def validate_email(self, value):
        if value and CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phonenumber', 'address']  
        extra_kwargs = {
            'email': {'required': False},
            'phonenumber': {'required': False},
            'address': {'required': False},
            'username': {'required': False}, 
        }

    def validate_phonenumber(self, value):
        user = self.context['request'].user
        if CustomUser.objects.exclude(pk=user.pk).filter(phonenumber=value).exists():
            raise serializers.ValidationError("Phone number already in use.")
        return value
    

    def validate_email(self, value):
        user = self.context['request'].user
        if CustomUser.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("Email already in use.")
        return value


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        user = self.context['request'].user

        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})

        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match."})

        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user




class StaffRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id','username', 'email', 'phonenumber', 'address', 'password', 'staff_id']

    def create(self, validated_data):
        validated_data['role'] = 2 
        user = CustomUser.objects.create_user(**validated_data)
        return user
    

class StaffProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phonenumber', 'address']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'phonenumber': {'required': False},
            'address': {'required': False},
        }

    def validate_email(self, value):
        user = self.context['request'].user
        if CustomUser.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("Email already in use.")
        return value

    def validate_username(self, value):
        user = self.context['request'].user
        if CustomUser.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("Username already in use.")
        return value



class RequestOtpSerializer(serializers.Serializer):
    username = serializers.CharField()

class VerifyOtpSerializer(serializers.Serializer):
    username = serializers.CharField()
    otp = serializers.CharField()

class ResetPasswordSerializer(serializers.Serializer):
    username = serializers.CharField()
    new_password = serializers.CharField()




class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ['id', 'name']


class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ['id','image']


class RoomSerializer(serializers.ModelSerializer):
    room_images = RoomImageSerializer(source='images', many=True, read_only=True)
    facilities = FacilitySerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = [
            'id', 'name', 'details', 'room_type', 'room_number',
            'price', 'category', 'status', 'cover_image',
            'facilities', 'room_images'
        ]

    def create(self, validated_data):
        request = self.context.get('request')

        # Create Room
        room = super().create(validated_data) # This will call the create method of ModelSerializer

        # Assign facilities
        facility_ids = request.data.getlist('facilities') # ['1', '2']
        room.facilities.set(Facility.objects.filter(id__in=facility_ids))

        # Add images
        images = request.FILES.getlist('room_images')
        for img in images:
            RoomImage.objects.create(room=room, image=img)

        return room

    def update(self, instance, validated_data):
        request = self.context.get('request')

        # Update Room fields
        instance = super().update(instance, validated_data) #	The existing Room object that you're updating

        # Update facilities
        facility_ids = request.data.getlist('facilities')
        instance.facilities.set(Facility.objects.filter(id__in=facility_ids)) #It replaces old facilities with the new ones.


        # Replace room images if new ones are uploaded
        images = request.FILES.getlist('room_images')
        if images:
            RoomImage.objects.filter(room=instance).delete()
            for img in images:
                RoomImage.objects.create(room=instance, image=img)

        return instance


class BookingSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    booking_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = Booking
        fields = ['booking_id', 'room', 'check_in', 'check_out', 'total_price']

    def validate(self, data):
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        room = data.get('room')

        if check_in >= check_out:
            raise serializers.ValidationError("Check-out must be after check-in.")

        if Booking.objects.filter(
            room=room,
            check_in__lt=check_out,
            check_out__gt=check_in,
            is_approved=True
        ).exists():
            raise serializers.ValidationError("Room is already booked for the selected dates.")

        return data
    


class PendingBookingSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source='id', read_only=True)
    room_id = serializers.IntegerField(source='room.id', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'booking_id',
            'room_id',
            'room_name',
            'username',
            'check_in',
            'check_out',
            'total_price',
        ]

class ApprovedBookingSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source='id')
    room_name = serializers.CharField(source='room.name', read_only=True)
    customer_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'booking_id',
            'room_name',
            'customer_name',
            'check_in',
            'check_out',
        ]

class RejectedBookingSerializer(serializers.ModelSerializer):
    booking_id = serializers.IntegerField(source='id')
    room_name = serializers.CharField(source='room.name', read_only=True)
    customer_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'booking_id',
            'room_name',
            'customer_name',
            'check_in',
            'check_out',
        ]

class RoomListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'name', 'price', 'room_number', 'room_type', 'status']  #




class AdminCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']

    def validate(self, attrs):
        if CustomUser.objects.filter(is_superuser=True).exists():
            raise serializers.ValidationError("Admin already exists.")
        return attrs

    def create(self, validated_data):
        return CustomUser.objects.create_superuser(**validated_data)




class UserBookingSerializer(serializers.ModelSerializer):
    room_name = serializers.CharField(source='room.name', read_only=True)
    status = serializers.SerializerMethodField()
    booked_for=serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'room_name', 'check_in', 'check_out', 'total_price', 'status','booked_for']

    def get_status(self, obj):
        if obj.is_approved:
            return "Approved"
        elif obj.is_rejected:
            return "Rejected"
        else:
            return "Pending"
        

class StaffBookingSerializer(serializers.ModelSerializer):
    room = RoomSerializer(read_only=True)  # full room data
    status = serializers.SerializerMethodField()
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'room','user', 'check_in', 'check_out', 'total_price', 'status']

    def get_status(self, obj):
        if obj.is_approved:
            return "Approved"
        elif obj.is_rejected:
            return "Rejected"
        return "Pending"        
        

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'is_read', 'created_at']


class ComplaintSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Complaint
        fields = ['id', 'user', 'message', 'is_resolved', 'created_at']


    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return Complaint.objects.create(**validated_data)
