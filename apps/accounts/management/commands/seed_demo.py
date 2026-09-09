"""
Seed demo companies, ERP support categories, priorities/SLA, and test users.

Safe to re-run — uses get_or_create / update_or_create throughout.

    python manage.py seed_demo
"""
from django.core.management.base import BaseCommand

from apps.accounts.models import Company, User
from apps.tickets.models import Category, Priority, SLAPolicy, SupportLayer

DEMO_PASSWORD = "Test@123"

COMPANIES = [
    {"name": "CCL", "short_code": "CCL"},
    {"name": "CCDL", "short_code": "CCDL"},
]

CATEGORIES = [
    "ERP Web Support",
    "ERP Mobile Support",
    "Others",
]

# rank: lower = higher urgency
PRIORITIES = [
    {"name": "Critical", "rank": 1},
    {"name": "High", "rank": 2},
    {"name": "Medium", "rank": 3},
    {"name": "Low", "rank": 4},
]

SUPPORT_LAYERS = [
    {
        "name": "Dev Team",
        "level": 1,
        "description": "All Developers",
    },
    {
        "name": "QA / BA / Support Team",
        "level": 2,
        "description": "All QA, BA, and Support Team members",
    },
]

# Priority-wide SLA defaults (minutes)
SLA_BY_PRIORITY = {
    "Critical": (15, 4 * 60),
    "High": (30, 8 * 60),
    "Medium": (60, 24 * 60),
    "Low": (120, 48 * 60),
}

# username, email, role, company short_code (or None for staff), first/last name
USERS = [
    ("ccl.user", "user@ccl.example.com", User.Role.CUSTOMER, "CCL", "CCL", "User"),
    ("ccdl.user", "user@ccdl.example.com", User.Role.CUSTOMER, "CCDL", "CCDL", "User"),
    ("agent1", "agent1@support.example.com", User.Role.AGENT, None, "Support", "Agent One"),
    ("agent2", "agent2@support.example.com", User.Role.AGENT, None, "Support", "Agent Two"),
    (
        "supervisor",
        "supervisor@support.example.com",
        User.Role.SUPERVISOR,
        None,
        "Support",
        "Supervisor",
    ),
    ("admin", "admin@support.example.com", User.Role.ADMIN, None, "System", "Admin"),
]

# username -> support layer levels
LAYER_MEMBERSHIP = {
    "agent1": [1],
    "agent2": [2],
    "supervisor": [1, 2],
    "admin": [1, 2],
}


class Command(BaseCommand):
    help = "Seed CCL/CCDL companies, ERP support categories, priorities, and test users."

    def handle(self, *args, **options):
        companies = self._seed_companies()
        self._seed_categories()
        priorities = self._seed_priorities()
        self._seed_sla_policies(priorities)
        layers = self._seed_support_layers()
        self._seed_users(companies)
        self._seed_layer_membership(layers)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo data ready. Test logins (password Test@123):"))
        for username, email, role, company_code, *_ in USERS:
            scope = company_code or "staff"
            self.stdout.write(f"  {username} / {email}  ({role}, {scope})")

    def _seed_companies(self):
        companies = {}
        for data in COMPANIES:
            company, created = Company.objects.get_or_create(
                short_code=data["short_code"],
                defaults={"name": data["name"], "is_active": True},
            )
            companies[company.short_code] = company
            verb = "Created" if created else "Exists"
            self.stdout.write(f"{verb} company: {company.name}")
        return companies

    def _seed_categories(self):
        wanted = set(CATEGORIES)
        for name in CATEGORIES:
            cat, created = Category.objects.update_or_create(
                name=name, defaults={"is_active": True}
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(f"{verb} category: {cat.name}")
        # Deactivate legacy categories not in the required set
        deactivated = Category.objects.exclude(name__in=wanted).filter(is_active=True).update(
            is_active=False
        )
        if deactivated:
            self.stdout.write(f"Deactivated {deactivated} legacy categor(ies)")

    def _seed_support_layers(self):
        layers = {}
        wanted_levels = {data["level"] for data in SUPPORT_LAYERS}
        for data in SUPPORT_LAYERS:
            layer, created = SupportLayer.objects.update_or_create(
                level=data["level"],
                defaults={
                    "name": data["name"],
                    "description": data["description"],
                    "is_active": True,
                },
            )
            layers[layer.level] = layer
            verb = "Created" if created else "Updated"
            self.stdout.write(f"{verb} support layer: {layer}")
        # Deactivate layers outside the new Dev / QA-BA-Support set
        SupportLayer.objects.exclude(level__in=wanted_levels).update(is_active=False)
        return layers

    def _seed_priorities(self):
        priorities = {}
        for data in PRIORITIES:
            priority, created = Priority.objects.get_or_create(
                name=data["name"],
                defaults={"rank": data["rank"]},
            )
            if not created and priority.rank != data["rank"]:
                priority.rank = data["rank"]
                priority.save(update_fields=["rank"])
            priorities[priority.name] = priority
            verb = "Created" if created else "Exists"
            self.stdout.write(f"{verb} priority: {priority.name}")
        return priorities

    def _seed_sla_policies(self, priorities):
        for name, (first_response, resolution) in SLA_BY_PRIORITY.items():
            policy, created = SLAPolicy.objects.get_or_create(
                priority=priorities[name],
                category=None,
                defaults={
                    "first_response_minutes": first_response,
                    "resolution_minutes": resolution,
                },
            )
            verb = "Created" if created else "Exists"
            self.stdout.write(f"{verb} SLA: {policy}")

    def _seed_users(self, companies):
        for username, email, role, company_code, first_name, last_name in USERS:
            company = companies[company_code] if company_code else None
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "role": role,
                    "company": company,
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            # Keep re-runs consistent for demo accounts without clobbering
            # unrelated profile edits beyond password/role/company/email.
            user.email = email
            user.role = role
            user.company = company
            user.first_name = first_name
            user.last_name = last_name
            user.set_password(DEMO_PASSWORD)
            if role in {User.Role.AGENT, User.Role.SUPERVISOR, User.Role.ADMIN}:
                user.is_staff = True
            if role == User.Role.ADMIN:
                user.is_superuser = True
            user.save()
            verb = "Created" if created else "Updated"
            self.stdout.write(f"{verb} user: {username} <{email}>")

    def _seed_layer_membership(self, layers):
        for username, level_list in LAYER_MEMBERSHIP.items():
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                continue
            membership = [layers[level] for level in level_list if level in layers]
            user.support_layers.set(membership)
            names = ", ".join(str(layer) for layer in membership)
            self.stdout.write(f"Layer membership: {username} -> {names}")
