"""Custom JWT obtain that accepts company and tries LDAP then local auth."""
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.ldap_auth import (
    authenticate_ldap,
    ldap_enabled,
    resolve_company_from_ldap,
    upsert_ldap_user,
)
from apps.accounts.models import Company, User


class CompanyTokenObtainPairSerializer(TokenObtainPairSerializer):
    company = serializers.CharField(
        required=True,
        help_text="Company short_code: ccl or ccdl",
    )

    def validate(self, attrs):
        username = attrs.get(self.username_field)
        password = attrs.get("password")
        company_code = (attrs.get("company") or "").strip().lower()

        company = Company.objects.filter(short_code__iexact=company_code, is_active=True).first()
        if not company:
            raise serializers.ValidationError({"company": "Unknown or inactive company."})

        user = None

        # 1) LDAP for cg-bd.com ERP users (UPN bind when enabled)
        if ldap_enabled():
            ldap_attrs = authenticate_ldap(username, password)
            if ldap_attrs:
                ldap_company = resolve_company_from_ldap(ldap_attrs, company_code)
                if ldap_company is None:
                    raise serializers.ValidationError(
                        {"company": "Could not resolve company for this LDAP user."}
                    )
                if ldap_company.short_code.lower() != company_code:
                    raise serializers.ValidationError(
                        {"company": "Selected company does not match your LDAP group."}
                    )
                user = upsert_ldap_user(ldap_attrs, ldap_company)

        # 2) Local Django user (agents, admins, demo customers)
        if user is None:
            if ldap_enabled() and not settings.LDAP_ALLOW_LOCAL_FALLBACK:
                raise serializers.ValidationError({"detail": "LDAP authentication failed."})
            user = authenticate(
                request=self.context.get("request"),
                username=username,
                password=password,
            )
            if user is None:
                raise serializers.ValidationError(
                    {"detail": "No active account found with the given credentials."}
                )
            if not user.is_active:
                raise serializers.ValidationError({"detail": "User account is disabled."})

            if user.is_customer:
                if not user.company_id or user.company.short_code.lower() != company_code:
                    raise serializers.ValidationError(
                        {"company": "Selected company does not match this account."}
                    )

        refresh = self.get_token(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class CompanyTokenObtainPairView(TokenObtainPairView):
    serializer_class = CompanyTokenObtainPairSerializer
