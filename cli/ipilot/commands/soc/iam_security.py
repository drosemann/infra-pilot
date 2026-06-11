import argparse
import json

def register_subparser(subparsers):
    parser = subparsers.add_parser("iam-security", help="IAM security operations", aliases=["iamsec"])
    parser.set_defaults(func=handle_iam_security)
    sub = parser.add_subparsers(dest="action")

    p_list = sub.add_parser("list", help="List users, roles, or access reviews")
    p_list.add_argument("resource", choices=["users", "roles", "access-reviews"])
    p_list.add_argument("--status", choices=["active", "inactive", "pending"])
    p_list.add_argument("--output", choices=["text", "json"], default="text")

    p_show = sub.add_parser("show", help="Show user or role details")
    p_show.add_argument("resource", choices=["user", "role", "access-review"])
    p_show.add_argument("id", help="Resource ID")
    p_show.add_argument("--output", choices=["text", "json"], default="text")

    p_create = sub.add_parser("create", help="Create a user")
    p_create.add_argument("username", help="Username")
    p_create.add_argument("--role", help="Assign role")
    p_create.add_argument("--mfa", choices=["true", "false"], default="true")

    p_update = sub.add_parser("update", help="Update user or role")
    p_update.add_argument("id", help="Resource ID")
    p_update.add_argument("--role", help="New role")
    p_update.add_argument("--status", choices=["active", "disabled"])

    p_delete = sub.add_parser("delete", help="Delete a user")
    p_delete.add_argument("id", help="User ID")

    p_execute = sub.add_parser("execute", help="Run access review")
    p_execute.add_argument("--review-id", help="Review ID to execute")

    p_report = sub.add_parser("report", help="Generate IAM security report")
    p_report.add_argument("--format", choices=["summary", "users", "roles", "access"], default="summary")
    p_report.add_argument("--output", choices=["text", "json"], default="text")

    p_export = sub.add_parser("export", help="Export IAM data")
    p_export.add_argument("--type", choices=["users", "roles", "reviews"], default="users")
    p_export.add_argument("--format", choices=["json", "csv"], default="json")

    p_health = sub.add_parser("health", help="Check IAM platform health")


def handle_iam_security(args):
    if args.action == "list":
        data = {"users": 245, "roles": 68, "access_reviews": 3}
        print(json.dumps(data, indent=2) if args.output == "json" else f"IAM {args.resource}: {data}")
    elif args.action == "show":
        info = {"id": args.id, "type": args.resource, "status": "active"}
        print(json.dumps(info, indent=2) if args.output == "json" else f"{args.resource.title()} {args.id}: {info}")
    elif args.action == "create":
        print(f"Created user {args.username} (mfa: [REDACTED])")
    elif args.action == "update":
        print(f"Updated resource {args.id}")
    elif args.action == "delete":
        print(f"Deleted user {args.id}")
    elif args.action == "execute":
        print(f"Executing access review {args.review_id}")
    elif args.action == "report":
        report_data = {"total_users": 245, "active": 218, "roles": 68, "mfa_rate": 98.8, "pending_reviews": 3, "privileged_users": 24}
        redacted = {k: "[REDACTED]" if k in ("mfa_rate", "privileged_users") else v for k, v in report_data.items()}
        if args.output == "json":
            print(json.dumps(redacted, indent=2))
        else:
            print(f"IAM {args.format.title()} Report")
            print(f"  Users: {report_data['total_users']} ({report_data['active']} active)")
            print(f"  Roles: {report_data['roles']}")
            print(f"  MFA Rate: [REDACTED]")
            print(f"  Privileged Users: [REDACTED]")
    elif args.action == "export":
        print(f"Exporting {args.type} as {args.format}")
    elif args.action == "health":
        health_info = {"status": "healthy", "mfa_adoption": "98.8%", "inactive_users": 27, "over_permissioned_roles": 7}
        redacted = {k: "[REDACTED]" if k in ("mfa_adoption", "over_permissioned_roles") else v for k, v in health_info.items()}
        print(json.dumps(redacted, indent=2))
