from django.contrib.auth.models import AbstractUser
from django.db import models


class Company(models.Model):
    """A client company we provide support to (e.g. CCL, CCDL)."""

    name = models.CharField(max_length=120, unique=True)
    short_code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "companies"
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    Custom user covering both customer contacts and internal staff.

    Kept as a single model (rather than separate Customer/Staff models) so
    auth, permissions, and the ticket FK stay simple — role determines
    what a user can see and do.
    """

    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        AGENT = "agent", "Support agent"
        SUPERVISOR = "supervisor", "Supervisor"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
        help_text="Required for customer users; blank for internal staff.",
    )
    phone = models.CharField(max_length=32, blank=True)

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    @property
    def is_staff_member(self):
        return self.role in {self.Role.AGENT, self.Role.SUPERVISOR, self.Role.ADMIN}

    def __str__(self):
        return self.get_full_name() or self.username
