import argparse
import json

def register_subparser(subparsers):
    parser = subparsers.add_parser("endpoint", help="Endpoint protection operations")
    parser.set_defaults(func=handle_endpoint)
    sub = parser.add_subparsers(dest="action")

    p_list = sub.add_parser("list", help="List devices, policies, or alerts")
    p_list.add_argument("resource", choices=["devices", "policies", "alerts"])
    p_list.add_argument("--status", choices=["online", "offline", "healthy", "critical"])
    p_list.add_argument("--output", choices=["text", "json"], default="text")

    p_show = sub.add_parser("show", help="Show device or alert details")
    p_show.add_argument("resource", choices=["device", "policy", "alert"])
    p_show.add_argument("id", help="Resource ID")
    p_show.add_argument("--output", choices=["text", "json"], default="text")

    p_create = sub.add_parser("create", help="Create a policy")
    p_create.add_argument("name", help="Policy name")
    p_create.add_argument("--type", choices=["av", "firewall", "dlp", "appctrl"], default="av")

    p_update = sub.add_parser("update", help="Update a device or policy")
    p_update.add_argument("id", help="Resource ID")
    p_update.add_argument("--policy", help="Assign policy ID")
    p_update.add_argument("--group", help="Device group")

    p_delete = sub.add_parser("delete", help="Delete a policy")
    p_delete.add_argument("id", help="Policy ID")

    p_execute = sub.add_parser("execute", help="Run scan on device")
    p_execute.add_argument("device_id", help="Device ID")
    p_execute.add_argument("--scan-type", choices=["quick", "full", "custom"], default="quick")

    p_report = sub.add_parser("report", help="Generate endpoint security report")
    p_report.add_argument("--format", choices=["summary", "compliance", "threats"], default="summary")
    p_report.add_argument("--output", choices=["text", "json"], default="text")

    p_export = sub.add_parser("export", help="Export endpoint data")
    p_export.add_argument("--type", choices=["devices", "alerts", "compliance"], default="devices")
    p_export.add_argument("--format", choices=["json", "csv"], default="json")

    p_health = sub.add_parser("health", help="Check endpoint protection health")


def handle_endpoint(args):
    if args.action == "list":
        data = {"devices": 342, "policies": 18, "alerts_24h": 43}
        print(json.dumps(data, indent=2) if args.output == "json" else f"Endpoint {args.resource}: {data}")
    elif args.action == "show":
        info = {"id": args.id, "type": args.resource, "status": "active"}
        print(json.dumps(info, indent=2) if args.output == "json" else f"{args.resource.title()} {args.id}: {info}")
    elif args.action == "create":
        print(f"Created {args.type} policy: {args.name}")
    elif args.action == "update":
        print(f"Updated resource {args.id}")
    elif args.action == "delete":
        print(f"Deleted policy {args.id}")
    elif args.action == "execute":
        print(f"Running {args.scan_type} scan on device {args.device_id}")
    elif args.action == "report":
        report_data = {"total_devices": 342, "online": 328, "offline": 14, "alerts_24h": 43, "compliance_rate": 93.6, "avg_risk_score": 24}
        if args.output == "json":
            print(json.dumps(report_data, indent=2))
        else:
            print(f"Endpoint {args.format.title()} Report")
            print(f"  Devices: {report_data['total_devices']} ({report_data['online']} online, {report_data['offline']} offline)")
            print(f"  Alerts (24h): {report_data['alerts_24h']}")
            print(f"  Compliance: {report_data['compliance_rate']}%")
    elif args.action == "export":
        print(f"Exporting {args.type} as {args.format}")
    elif args.action == "health":
        health_info = {"status": "healthy", "online_devices": 328, "offline_devices": 14, "avg_risk_score": 24, "last_full_scan": "2024-12-15 04:00 UTC"}
        print(json.dumps(health_info, indent=2))
