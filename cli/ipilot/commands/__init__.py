"""Infrastructure command registrations.

Only commands with a functioning backend API are registered here.
"""

from ..core.command_registry import register
from .infrastructure.backup import app as backup_app
from .infrastructure.deployment import app as deploy_app
from .infrastructure.logs import app as logs_app
from .infrastructure.server import app as server_app

register("server", "Server management")(server_app)
register("backup", "Backup management")(backup_app)
register("deploy", "Deployment")(deploy_app)
register("logs", "Logs")(logs_app)

from .apikeys import app as apikeys_app
from .alerts import app as alerts_app
from .audit import app as audit_app
from .databases import app as databases_app
from .doctor import app as doctor_app
from .gitops import app as gitops_app
from .inventory import app as inventory_app
from .maintenance import app as maintenance_app
from .metrics import app as metrics_app
from .notifications import app as notifications_app
from .orgs import app as orgs_app
from .pet import app as pet_app
from .plugins import app as plugins_app
from .reports import app as reports_app
from .rollback import app as rollback_app
from .runbooks import app as runbooks_app
from .secrets import app as secrets_app
from .ssh import app as ssh_app
from .templates import app as templates_app
from .two_factor import app as two_factor_app
from .tui import app as tui_app
from .webhooks import app as webhooks_app

register("gitops", "Infrastructure as Code (GitOps)")(gitops_app)
register("ssh", "SSH session management")(ssh_app)
register("inventory", "Server inventory")(inventory_app)
register("secrets", "Secret management")(secrets_app)
register("plugins", "Plugin management")(plugins_app)
register("doctor", "System diagnostics")(doctor_app)
register("webhooks", "Webhook management")(webhooks_app)
register("apikeys", "API key management")(apikeys_app)
register("templates", "Deployment templates")(templates_app)
register("tui", "Terminal UI mode")(tui_app)
register("rollback", "Undo/rollback changes")(rollback_app)
register("metrics", "Resource metrics")(metrics_app)
register("alerts", "Alert rules and incidents")(alerts_app)
register("audit", "Audit log")(audit_app)
register("runbooks", "Operational runbooks")(runbooks_app)
register("maintenance", "Maintenance windows")(maintenance_app)
register("notifications", "Notification channels")(notifications_app)
register("orgs", "Organizations")(orgs_app)
register("databases", "Managed databases")(databases_app)
register("reports", "Usage reports")(reports_app)
register("two-factor", "Two-factor authentication")(two_factor_app)
register("pet", "Living Fleet creature status")(pet_app)

__all__: list[str] = [
    "server_app",
    "backup_app",
    "deploy_app",
    "logs_app",
    "gitops_app",
    "ssh_app",
    "inventory_app",
    "secrets_app",
    "plugins_app",
    "doctor_app",
    "webhooks_app",
    "apikeys_app",
    "templates_app",
    "tui_app",
    "rollback_app",
    "metrics_app",
    "alerts_app",
    "audit_app",
    "runbooks_app",
    "maintenance_app",
    "notifications_app",
    "orgs_app",
    "databases_app",
    "reports_app",
    "two_factor_app",
    "pet_app",
]
