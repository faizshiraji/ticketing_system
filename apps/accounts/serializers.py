from rest_framework import serializers

from .models import Company, User


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "short_code", "is_active", "created_at"]
        read_only_fields = ["created_at"]


class UserSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "company",
            "phone",
        ]
        read_only_fields = ["role"]


class MeSerializer(UserSerializer):
    """What /api/accounts/me/ returns — same shape, kept separate so it can
    diverge later (e.g. adding notification preferences) without touching
    the general-purpose UserSerializer."""


class StaffAgentSerializer(UserSerializer):
    """Staff list for escalation pickers, includes support layer memberships."""

    support_layers = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["support_layers"]

    def get_support_layers(self, user):
        return [
            {"id": layer.id, "name": layer.name, "level": layer.level}
            for layer in user.support_layers.filter(is_active=True).order_by("level")
        ]


class UserAdminSerializer(serializers.ModelSerializer):
    """Admin/supervisor user management — nested company on read, PK on write."""

    company = CompanySerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source="company",
        write_only=True,
        required=False,
        allow_null=True,
    )
    password = serializers.CharField(write_only=True, required=False, allow_blank=False, min_length=8)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "company",
            "company_id",
            "phone",
            "is_active",
            "password",
        ]

    def validate(self, attrs):
        role = attrs.get("role", getattr(self.instance, "role", None))
        company = attrs.get("company", getattr(self.instance, "company", None))
        if "company" in attrs or "role" in attrs or self.instance is None:
            if role == User.Role.CUSTOMER and company is None:
                raise serializers.ValidationError({"company_id": "Customers must belong to a company."})
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "Password is required when creating a user."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
