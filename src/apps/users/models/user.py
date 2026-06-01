from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):

        if not email:
            raise ValueError('El correo electrónico es obligatorio')

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            **extra_fields
        )

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(
            email,
            password,
            **extra_fields
        )


class User(AbstractUser):

    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        STUDENT = 'STUDENT', 'Estudiante'
        TEACHER = 'TEACHER', 'Docente'

    username = None

    email = models.EmailField(
        unique=True
    )

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.STUDENT
    )

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def is_admin_role(self):
        return self.role == self.Roles.ADMIN

    @property
    def is_teacher_role(self):
        return self.role == self.Roles.TEACHER

    @property
    def is_student_role(self):
        return self.role == self.Roles.STUDENT

    @property
    def unread_notifications_count(self):
        return self.notifications.filter(is_read=False).count()
