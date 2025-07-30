from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin, Group
from django.core.validators import RegexValidator

# Create your models here.

class UserManager(BaseUserManager):
    """Manager personalizado para usuarios que usan email como nombre de usuario."""

    def create_user(self, email, password=None, **extra_fields):
        """Crea y guarda un usuario con el email y la contraseña dados."""
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, email, password=None, **extra_fields):
        """Crea y guarda un superusuario con el email y la contraseña dados."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

class Usuario(AbstractUser, PermissionsMixin):
    """Modelo de usuario
    Heredamos de AbstractUser, cambiamos el campo username con email y añadimos algunos campos extra
    """

    email = models.EmailField(
        'email address',
        unique=True,
        error_messages={'unique': 'Un usuario ya existe con este email'}
    )
    tfno_regex = RegexValidator(
        regex=r'\+?1?\d{9,11}$',
        message="Telefono en el formato +99999999999, hasta 11 digitos"
    )
    numero_telefono = models.CharField(
        validators=[tfno_regex], max_length=11, blank=True
    )
    verificado = models.BooleanField(
        'verificado',
        default=True,
        help_text='Configurado a True cuando el usuario ha verificado su email'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    is_staff = models.BooleanField(default=False, verbose_name='Staff')
    groups = models.ManyToManyField(Group, blank=True, related_name='custom_user_set')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # Se indica que el UserManager será el administrador de objetos por defecto para ese modelo.
    objects = UserManager()

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return str(self.email)
