"""LDAP authentication against cg-bd.com Active Directory.

Env schema aligned with the working ERP LDAP stack:
  LDAP_URI / LDAP_BASE_DN / LDAP_BIND_FORMAT=upn / LDAP_UPN_SUFFIX / …

When LDAP_ENABLED is false or bind fails and LDAP_ALLOW_LOCAL_FALLBACK is
true, callers fall back to Django ModelBackend.
"""
from __future__ import annotations

import logging
import ssl

import ldap3
from django.conf import settings
from django.db import transaction
from ldap3 import Tls
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars

from apps.accounts.models import Company, User

logger = logging.getLogger(__name__)


def ldap_enabled() -> bool:
    return bool(getattr(settings, "LDAP_ENABLED", False) and settings.LDAP_SERVER_URI)


def _log(msg: str, *args):
    if getattr(settings, "LDAP_LOGGING", False):
        logger.info(msg, *args)
    else:
        logger.debug(msg, *args)


def _tls_config() -> Tls | None:
    if not (settings.LDAP_USE_SSL or settings.LDAP_USE_STARTTLS):
        return None
    mode = (getattr(settings, "LDAP_TLS_REQUIRE_CERT", "demand") or "demand").lower()
    validate = {
        "demand": ssl.CERT_REQUIRED,
        "required": ssl.CERT_REQUIRED,
        "allow": ssl.CERT_OPTIONAL,
        "never": ssl.CERT_NONE,
        "try": ssl.CERT_OPTIONAL,
    }.get(mode, ssl.CERT_REQUIRED)
    return Tls(validate=validate, version=ssl.PROTOCOL_TLS_CLIENT)


def _server() -> ldap3.Server:
    return ldap3.Server(
        settings.LDAP_SERVER_URI,
        use_ssl=settings.LDAP_USE_SSL,
        tls=_tls_config(),
        get_info=ldap3.NONE,
        connect_timeout=settings.LDAP_CONNECT_TIMEOUT,
    )


def _user_bind_identity(username: str) -> str:
    """How we present the user to LDAP for a direct bind."""
    fmt = (getattr(settings, "LDAP_BIND_FORMAT", "upn") or "upn").lower()
    bare = username.split("@", 1)[0]
    if fmt == "upn":
        suffix = getattr(settings, "LDAP_UPN_SUFFIX", "cg-bd.com") or "cg-bd.com"
        if "@" in username:
            return username
        return f"{bare}@{suffix}"
    if fmt == "dn" and settings.LDAP_USER_DN_TEMPLATE:
        return settings.LDAP_USER_DN_TEMPLATE.format(username=bare)
    return username


def authenticate_ldap(username: str, password: str) -> dict | None:
    """
    Authenticate against AD/LDAP. Prefer UPN bind (user@cg-bd.com) to match
    the working ERP project. Returns profile attrs on success, else None.
    """
    if not ldap_enabled() or not username or not password:
        return None

    bare = username.split("@", 1)[0]
    server = _server()
    bind_format = (getattr(settings, "LDAP_BIND_FORMAT", "upn") or "upn").lower()

    try:
        # --- Primary: direct user bind (UPN / DN template) ---
        if bind_format in {"upn", "dn"} or settings.LDAP_USER_DN_TEMPLATE:
            identity = _user_bind_identity(username)
            _log("LDAP user bind as %s", identity)
            conn = ldap3.Connection(
                server,
                user=identity,
                password=password,
                auto_bind=True,
                raise_exceptions=True,
            )
            if settings.LDAP_USE_STARTTLS and not settings.LDAP_USE_SSL:
                conn.start_tls()

            entry = _fetch_user_entry(conn, bare, identity)
            attrs = _entry_to_attrs(entry, bare)
            conn.unbind()
            return attrs

        # --- Fallback: service-account search then user bind ---
        bind_dn = settings.LDAP_BIND_DN
        bind_password = settings.LDAP_BIND_PASSWORD
        if getattr(settings, "LDAP_REQUIRE_SERVICE_BIND", False) and not bind_dn:
            logger.warning("LDAP_REQUIRE_SERVICE_BIND set but LDAP_BIND_DN is empty")
            return None
        if not bind_dn:
            logger.warning("LDAP_BIND_DN required for search-bind mode")
            return None

        admin = ldap3.Connection(
            server,
            user=bind_dn,
            password=bind_password,
            auto_bind=True,
            raise_exceptions=True,
        )
        filt = settings.LDAP_USER_SEARCH_FILTER.format(username=escape_filter_chars(bare))
        admin.search(settings.LDAP_USER_SEARCH_BASE, filt, attributes=settings.LDAP_ATTRS)
        if not admin.entries:
            admin.unbind()
            return None
        entry = admin.entries[0]
        user_dn = entry.entry_dn
        admin.unbind()

        conn = ldap3.Connection(
            server,
            user=user_dn,
            password=password,
            auto_bind=True,
            raise_exceptions=True,
        )
        attrs = _entry_to_attrs(entry, bare)
        conn.unbind()
        return attrs
    except LDAPException:
        logger.exception("LDAP authentication failed for %s", username)
        return None
    except Exception:
        logger.exception("LDAP authentication failed for %s", username)
        return None


def _fetch_user_entry(conn: ldap3.Connection, bare: str, identity: str):
    """Load directory attributes after a successful user bind."""
    base = settings.LDAP_USER_SEARCH_BASE or settings.LDAP_BASE_DN
    if base:
        filt = settings.LDAP_USER_SEARCH_FILTER.format(username=escape_filter_chars(bare))
        conn.search(base, filt, attributes=settings.LDAP_ATTRS, size_limit=1)
        if conn.entries:
            return conn.entries[0]
    # Try reading the bound identity as a DN (only works for DN binds)
    if identity.lower().startswith("cn=") or "dc=" in identity.lower():
        conn.search(identity, "(objectClass=*)", search_scope=ldap3.BASE, attributes=settings.LDAP_ATTRS)
        if conn.entries:
            return conn.entries[0]
    return None


def _entry_to_attrs(entry, username: str) -> dict:
    def first(name, default=""):
        if entry is None:
            return default
        try:
            val = entry[name].value
            if isinstance(val, list):
                return val[0] if val else default
            return val if val is not None else default
        except Exception:
            return default

    email = first("mail") or first("userPrincipalName") or ""
    if email and "@" not in str(email):
        email = f"{username}@{settings.LDAP_EMAIL_DOMAIN}"
    if not email:
        email = f"{username}@{settings.LDAP_EMAIL_DOMAIN}"

    return {
        "username": username,
        "email": str(email),
        "first_name": str(first("givenName") or ""),
        "last_name": str(first("sn") or ""),
        "phone": str(first("telephoneNumber") or first("mobile") or ""),
        "member_of": _member_of(entry),
    }


def _member_of(entry) -> list[str]:
    if entry is None:
        return []
    try:
        val = entry["memberOf"].value
        if val is None:
            return []
        if isinstance(val, list):
            return [str(v) for v in val]
        return [str(val)]
    except Exception:
        return []


def resolve_company_from_ldap(attrs: dict, selected_short_code: str) -> Company | None:
    """
    Map LDAP groups to company when LDAP_COMPANY_GROUP_MAP is set;
    otherwise trust the company selected on the login form.
    """
    group_map = getattr(settings, "LDAP_COMPANY_GROUP_MAP", {}) or {}
    member_of = [m.lower() for m in attrs.get("member_of") or []]
    matched_code = None
    for group_dn, code in group_map.items():
        if group_dn.lower() in member_of or any(group_dn.lower() in m for m in member_of):
            matched_code = code.lower()
            break

    code = (matched_code or selected_short_code or "").lower()
    if not code:
        return None
    return Company.objects.filter(short_code__iexact=code, is_active=True).first()


@transaction.atomic
def upsert_ldap_user(attrs: dict, company: Company) -> User:
    """Create or update a local User from LDAP attrs as a customer of company."""
    username = attrs["username"]
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": attrs.get("email") or "",
            "first_name": attrs.get("first_name") or "",
            "last_name": attrs.get("last_name") or "",
            "phone": attrs.get("phone") or "",
            "role": User.Role.CUSTOMER,
            "company": company,
            "is_active": True,
        },
    )
    if not created:
        user.email = attrs.get("email") or user.email
        user.first_name = attrs.get("first_name") or user.first_name
        user.last_name = attrs.get("last_name") or user.last_name
        user.phone = attrs.get("phone") or user.phone
        if not user.is_staff_member:
            user.role = User.Role.CUSTOMER
            user.company = company
        user.is_active = True
        user.save()
    if not user.is_staff_member:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user
