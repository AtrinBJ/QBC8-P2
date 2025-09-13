from django.db import models

class User(models.Model):
    phoneNumber = models.CharField(max_length=21, unique=True)
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.firstName} {self.lastName}"

class UserExtra(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="extra")
    birthday = models.DateField(null=True)
    picture = models.CharField(max_length=255, null=True)
    sex = [
    ('M', 'Male'),
    ('F', 'Female')]
    sex = models.CharField(max_length=1, choices=sex, null=True)
    nationalCode = models.CharField(max_length=10, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Extra for {self.user}"