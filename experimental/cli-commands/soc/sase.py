import argparse
import json

def register_subparser(subparsers):
    parser = subparsers.add_parser("sase", help="Secure Access Service Edge operations")
    parser.set_defaults(func=handle_sase)
    sub = parser.add_subparsers(dest="action")

    p_list = sub.add_parser("list", help="List policies, branches, or ZTNA apps")
    p_list.add_argument("resource", choices=["policies", "branches", "ztna"])
    p_list.add_argument("--output", choices=["text", "json"], default="text")

    p_show = sub.add_parser("show", help="Show policy or branch details")
    p_show.add_argument("resource", choices=["policy", "branch", "ztna-app"])
    p_show.add_argument("id", help="Resource ID")
    p_show.add_argument("--output", choices=["text", "json"], default="text")

    p_create = sub.add_parser("create", help="Create a policy")
    p_create.add_argument("name", help="Policy name")
    p_create.add_argument("--type", choices=["security", "access", "traffic"], default="security")
    p_create.add_argument("--enabled", choices=["true", "false"], default="true")

    p_update = sub.add_parser("update", help="Update a policy")
    p_update.add_argument("id", help="Policy ID")
    p_update.add_argument("--enabled", choices=["true", "false"])

    p_delete = sub.add_parser("delete", help="Delete a policy")
    p_delete.add_argument("id", help="Policy ID")

    p_execute = sub.add_parser("execute", help="Test policy against traffic")
    p_execute.add_argument("policy_id", help="Policy ID")
    p_execute.add_argument("--source-ip", default="10.0.0.1")
    p_execute.add_argument("--dest-ip", default="8.8.8.8")

    p_report = sub.add_parser("report", help="Generate SASE report")
    p_report.add_argument("--format", choices=["summary", "policy", "traffic"], default="summary")
    p_report.add_argument("--output", choices=["text", "json"], default="text")

    p_export = sub.add_parser("export", help="Export SASE data")
    p_export.add_argument("--type", choices=["policies", "branches", "ztna"], default="policies")
    p_export.add_argument("--format", choices=["json", "csv"], default="json")

    p_health = sub.add_parser("health", help="Check SASE platform health")


def handle_sase(args):
    if args.action == "list":
        data = {"policies": 24, "branches": 15, "ztna_apps": 32}
        print(json.dumps(data, indent=2) if args.output == "json" else f"SASE {args.resource}: {data}")
    elif args.action == "show":
        info = {"id": args.id, "type": args.resource, "status": "active"}
        print(json.dumps(info, indent=2) if args.output == "json" else f"{args.resource.title()} {args.id}: {info}")
    elif args.action == "create":
        print(f"Created {args.type} policy: {args.name} (enabled: {args.enabled})")
    elif args.action == "update":
        print(f"Updated policy {args.id}")
    elif args.action == "delete":
        print(f"Deleted policy {args.id}")
    elif args.action == "execute":
        print(f"Testing policy {args.policy_id} on traffic {args.source_ip} -> {args.dest_ip}")
    elif args.action == "report":
        report_data = {"total_policies": 24, "enabled": 20, "branches": 15, "ztna_apps": 32, "threats_blocked_24h": 89, "uptime": 99.97}
        if args.output == "json":
            print(json.dumps(report_data, indent=2))
        else:
            print(f"SASE {args.format.title()} Report")
            print(f"  Policies: {report_data['total_policies']} ({report_data['enabled']} enabled)")
            print(f"  Branches: {report_data['branches']} | ZTNA Apps: {report_data['ztna_apps']}")
            print(f"  Threats Blocked (24h): {report_data['threats_blocked_24h']} | Uptime: {report_data['uptime']}%")
    elif args.action == "export":
        print(f"Exporting {args.type} as {args.format}")
    elif args.action == "health":
        health_info = {"status": "healthy", "branches_online": 15, "uptime": "99.97%", "avg_latency": "12ms", "threats_blocked": 89}
        print(json.dumps(health_info, indent=2))
