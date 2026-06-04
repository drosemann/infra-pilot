import argparse
import json

def register_subparser(subparsers):
    parser = subparsers.add_parser("siem", help="SIEM platform operations")
    parser.set_defaults(func=handle_siem)
    sub = parser.add_subparsers(dest="action")

    p_list = sub.add_parser("list", help="List sources, alerts, or rules")
    p_list.add_argument("resource", choices=["sources", "alerts", "rules"])
    p_list.add_argument("--output", choices=["text", "json"], default="text")

    p_show = sub.add_parser("show", help="Show source, alert, or rule details")
    p_show.add_argument("resource", choices=["source", "alert", "rule"])
    p_show.add_argument("id", help="Resource ID")
    p_show.add_argument("--output", choices=["text", "json"], default="text")

    p_create = sub.add_parser("create", help="Create a correlation rule")
    p_create.add_argument("name", help="Rule name")
    p_create.add_argument("--severity", choices=["low", "medium", "high", "critical"], default="medium")
    p_create.add_argument("--query", default="*", help="Search query pattern")

    p_update = sub.add_parser("update", help="Update a rule")
    p_update.add_argument("id", help="Rule ID")
    p_update.add_argument("--enabled", choices=["true", "false"])

    p_delete = sub.add_parser("delete", help="Delete a rule")
    p_delete.add_argument("id", help="Rule ID")

    p_execute = sub.add_parser("execute", help="Execute a search query")
    p_execute.add_argument("query", help="Search query")
    p_execute.add_argument("--timeframe", default="24h", help="Time range (e.g. 24h, 7d)")

    p_report = sub.add_parser("report", help="Generate SIEM report")
    p_report.add_argument("--format", choices=["summary", "alerts", "sources"], default="summary")
    p_report.add_argument("--output", choices=["text", "json"], default="text")

    p_export = sub.add_parser("export", help="Export SIEM data")
    p_export.add_argument("--type", choices=["alerts", "events", "rules"], default="alerts")
    p_export.add_argument("--format", choices=["json", "csv"], default="json")

    p_health = sub.add_parser("health", help="Check SIEM platform health")


def handle_siem(args):
    if args.action == "list":
        data = {"sources": 34, "alerts_24h": 156, "rules": 78}
        print(json.dumps(data, indent=2) if args.output == "json" else f"SIEM {args.resource}: {data}")
    elif args.action == "show":
        info = {"id": args.id, "type": args.resource, "status": "active"}
        print(json.dumps(info, indent=2) if args.output == "json" else f"{args.resource.title()} {args.id}: {info}")
    elif args.action == "create":
        print(f"Created rule: {args.name} (severity: {args.severity})")
    elif args.action == "update":
        print(f"Updated rule {args.id}")
    elif args.action == "delete":
        print(f"Deleted rule {args.id}")
    elif args.action == "execute":
        print(f"Executing query '{args.query}' over {args.timeframe}")
    elif args.action == "report":
        report_data = {"sources": 34, "sources_online": 32, "alerts_24h": 156, "rules": 78, "rules_enabled": 72, "events_per_day": 1200000000}
        if args.output == "json":
            print(json.dumps(report_data, indent=2))
        else:
            print(f"SIEM {args.format.title()} Report")
            print(f"  Sources: {report_data['sources']} ({report_data['sources_online']} online)")
            print(f"  Alerts (24h): {report_data['alerts_24h']}")
            print(f"  Rules: {report_data['rules']} ({report_data['rules_enabled']} enabled)")
            print(f"  Events/Day: {report_data['events_per_day']}")
    elif args.action == "export":
        print(f"Exporting {args.type} as {args.format}")
    elif args.action == "health":
        health_info = {"status": "healthy", "sources_online": 32, "sources_offline": 2, "ingestion_rate": "98.7%", "storage_used": "4.2TB/10TB"}
        print(json.dumps(health_info, indent=2))
