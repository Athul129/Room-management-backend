from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager,PermissionsMixin
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

# Create your models here.
class CustomUsermanager(BaseUserManager):
	def create_user(self, username, email=None, password=None, **extra_fields):    
		if not username:
			raise ValueError('user must have username')
		if not password:
			raise ValueError('user must have a password') 
		email=self.normalize_email(email)

		user = self.model(username=username, email=email, **extra_fields)  
		user.set_password(password)  
		user.save(using=self._db)  
		return user 

	


	def create_superuser(self, username,email=None, password=None, **extra_fields):
		extra_fields.setdefault('is_staff',True)
		extra_fields.setdefault('is_superuser',True)
		extra_fields.setdefault('role', 1)

		if not password:
			raise ValueError("Superusers must have a password.")
			
		return self.create_user(username,email,password,**extra_fields)




ROLE_CHOICES = [
	(1, "Admin"),
	(2, "Staff"),
	(3, "User"),
]


class CustomUser(AbstractBaseUser,PermissionsMixin):
	username=models.CharField(max_length=100,unique=True)
	email=models.EmailField(blank=True,null=True)
	phonenumber=models.CharField(max_length=10,unique=True,null=True, blank=True)
	address=models.CharField(max_length=200)
	staff_id = models.CharField(max_length=50, blank=True, null=True)  

	is_active=models.BooleanField(default=True)
	is_superuser=models.BooleanField(default=False)
	is_staff=models.BooleanField(default=False)


	role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, default=3)
	objects=CustomUsermanager()


	USERNAME_FIELD = 'username'
	EMAIL_FIELD='email'
	REQUIRED_FIELDS=['email']


	def __str__(self):
		return self.username


class PasswordResetOtp(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=2)

    def __str__(self):
        return f"{self.user.username} - {self.otp}"


class Facility(models.Model):
      name=models.CharField(max_length=100, unique=True)

      def __str__(self):
            return self.name



class Room(models.Model):
    ROOM_TYPES = [
        ('single', 'Single'),
        ('double', 'Double'),
        ('suite', 'Suite'),
    ]

    ROOM_CATEGORIES = [
        ('ac', 'AC'),
        ('non_ac', 'Non-AC'),
    ]

    ROOM_STATUSES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('maintenance', 'Maintenance'),
    ]

    name = models.CharField(max_length=255)  
    details = models.TextField(null=True, blank=True) 
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, null=True, blank=True)
    room_number = models.CharField(max_length=20, unique=True)
    price = models.IntegerField(null=True, blank=True)  
    category = models.CharField(max_length=10, choices=ROOM_CATEGORIES, null=True, blank=True)
    status = models.CharField(max_length=15, choices=ROOM_STATUSES, default='available')

    cover_image=models.ImageField(upload_to="cover_images/", null=True,blank=True)

    facilities = models.ManyToManyField(Facility, blank=True) 

    def __str__(self):
        return f"{self.name} ({self.room_number})"

class RoomImage(models.Model):
    room = models.ForeignKey(Room, related_name="images", on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to="images", null=True, blank=True)  

    def __str__(self):
        return f"Image for {self.room.name} ({self.room.room_number})" if self.room else "Unassigned Image"
    


User = get_user_model()  # Using custom user model

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # User who booked the room
    room = models.ForeignKey("Room", on_delete=models.CASCADE)  
    check_in = models.DateField()  
    check_out = models.DateField()  
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  #  stores a decimal number    decimal place 2= This defines how many digits are reserved for the decimal part. Here, 2 decimal places are used, meaning values will be stored in the format XXXXXX.XX (e.g., 12345678.99).
    is_approved = models.BooleanField(default=False)  
    is_rejected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)  

    booked_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings_made_by_staff', null=True, blank=True) 

    def __str__(self):
        return f"{self.user.username} - {self.room.name} ({self.check_in} to {self.check_out})"
    


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"


class Complaint(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Complaint by {self.user.username}"