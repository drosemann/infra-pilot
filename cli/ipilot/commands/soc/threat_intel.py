import argparse
import json

def register_subparser(subparsers):
    parser = subparsers.add_parser("threat-intel", help="Threat Intelligence Platform operations", aliases=["tip"])
    parser.set_defaults(func=handle_threat_intel)
    sub = parser.add_subparsers(dest="action")

    p_list = sub.add_parser("list", help="List IoCs, feeds, or actors")
    p_list.add_argument("resource", choices=["iocs", "feeds", "actors"])
    p_list.add_argument("--output", choices=["text", "json"], default="text")

    p_show = sub.add_parser("show", help="Show IoC or actor details")
    p_show.add_argument("resource", choices=["ioc", "feed", "actor"])
    p_show.add_argument("id", help="Resource ID")
    p_show.add_argument("--output", choices=["text", "json"], default="text")

    p_create = sub.add_parser("create", help="Add an IoC")
    p_create.add_argument("type", choices=["ip", "domain", "hash", "url"], help="IoC type")
    p_create.add_argument("value", help="IoC value")
    p_create.add_argument("--confidence", type=int, default=75, help="Confidence score 0-100")

    p_update = sub.add_parser("update", help="Update an IoC")
    p_update.add_argument("id", help="IoC ID")
    p_update.add_argument("--confidence", type=int, help="New confidence score")

    p_delete = sub.add_parser("delete", help="Delete an IoC")
    p_delete.add_argument("id", help="IoC ID")

    p_execute = sub.add_parser("execute", help="Enrich an IoC")
    p_execute.add_argument("value", help="IoC value to enrich")
    p_execute.add_argument("--sources", nargs="+", default=["virustotal"], help="Enrichment sources")

    p_report = sub.add_parser("report", help="Generate threat intel report")
    p_report.add_argument("--format", choices=["summary", "iocs", "feeds"], default="summary")
    p_report.add_argument("--output", choices=["text", "json"], default="text")

    p_export = sub.add_parser("export", help="Export threat intel data")
    p_export.add_argument("--type", choices=["iocs", "feeds", "actors"], default="iocs")
    p_export.add_argument("--format", choices=["json", "csv", "stix"], default="json")

    p_health = sub.add_parser("health", help="Check threat intel platform health")


def handle_threat_intel(args):
    if args.action == "list":
        data = {"total_iocs": 1247, "feeds": 12, "actors": 8}
        print(json.dumps(data, indent=2) if args.output == "json" else f"Threat Intel {args.resource}: {data}")
    elif args.action == "show":
        info = {"id": args.id, "type": args.resource, "value": "example", "confidence": 85}
        print(json.dumps(info, indent=2) if args.output == "json" else f"{args.resource.title()} {args.id}: {info}")
    elif args.action == "create":
        print(f"Added IoC: {args.type} = {args.value} (confidence: {args.confidence})")
    elif args.action == "update":
        print(f"Updated IoC {args.id}")
    elif args.action == "delete":
        print(f"Deleted IoC {args.id}")
    elif args.action == "execute":
        print(f"Enriching {args.value} from sources: {args.sources}")
    elif args.action == "report":
        report_data = {"total_iocs": 1247, "new_24h": 89, "active_feeds": 12, "enrichment_rate": 62.0, "correlated_alerts": 42}
        if args.output == "json":
            print(json.dumps(report_data, indent=2))
        else:
            print(f"Threat Intel {args.format.title()} Report")
            print(f"  IoCs: {report_data['total_iocs']} ({report_data['new_24h']} new in 24h)")
            print(f"  Feeds: {report_data['active_feeds']} active ({report_data['enrichment_rate']}% enrichment)")
            print(f"  Correlated Alerts: {report_data['correlated_alerts']}")
    elif args.action == "export":
        print(f"Exporting {args.type} as {args.format}")
    elif args.action == "health":
        health_info = {"status": "healthy", "feeds_healthy": 11, "feeds_degraded": 1, "last_feed_update": "2024-12-15 11:45 UTC"}
        print(json.dumps(health_info, indent=2))
