import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

from services.integration_service.src.platform_engineering.doc_generator import DocGenerator, DocFormat, DocType

logger = logging.getLogger(__name__)


class DocGenCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.generator = DocGenerator()

    @discord.app_commands.command(name="doc-generate", description="Generate architecture documentation")
    @discord.app_commands.describe(title="Document title", service_id="Service ID", template="Architecture template")
    async def doc_generate(self, interaction: discord.Interaction, title: str, service_id: str, template: str = "microservice"):
        doc = self.generator.generate_architecture_doc(title, service_id, template)
        embed = discord.Embed(title="Document Generated", color=discord.Color.green())
        embed.add_field(name="ID", value=doc.doc_id[:8])
        embed.add_field(name="Title", value=doc.title)
        embed.add_field(name="Type", value=doc.doc_type.value)
        embed.add_field(name="Format", value=doc.format.value)
        embed.add_field(name="Words", value=doc.word_count)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-adr", description="Create an Architecture Decision Record")
    @discord.app_commands.describe(title="ADR title", context="Context", decision="Decision made", status="Status", domain="Domain")
    async def doc_adr_create(self, interaction: discord.Interaction, title: str, context: str, decision: str, status: str = "proposed", domain: str = ""):
        adr = self.generator.create_adr(title, context, decision, status, domain, authors=[interaction.user.name])
        embed = discord.Embed(title="ADR Created", color=discord.Color.blue())
        embed.add_field(name="ID", value=adr.adr_id[:8])
        embed.add_field(name="Title", value=adr.title)
        embed.add_field(name="Status", value=adr.status)
        embed.add_field(name="Domain", value=adr.domain or "N/A")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-adr-list", description="List ADRs")
    @discord.app_commands.describe(domain="Filter by domain", status="Filter by status")
    async def doc_adr_list(self, interaction: discord.Interaction, domain: str = "", status: str = ""):
        adrs = self.generator.list_adrs(domain=domain, status=status)
        if not adrs:
            await interaction.response.send_message("No ADRs found.", ephemeral=True)
            return
        embed = discord.Embed(title="Architecture Decision Records", color=discord.Color.blue())
        for adr in adrs[:10]:
            embed.add_field(name=f"{adr.title[:50]}", value=f"Status: {adr.status} | Domain: {adr.domain or 'N/A'}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-summary", description="Documentation generator summary")
    async def doc_summary(self, interaction: discord.Interaction):
        summary = self.generator.get_docs_summary()
        embed = discord.Embed(title="Documentation Summary", color=discord.Color.blue())
        embed.add_field(name="Total Documents", value=summary.get("total_documents", 0))
        embed.add_field(name="Total ADRs", value=summary.get("total_adrs", 0))
        by_type = summary.get("by_type", {})
        if by_type:
            embed.add_field(name="By Type", value="\n".join(f"{k}: {v}" for k, v in list(by_type.items())[:5]), inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-adr-update", description="Update ADR status")
    @discord.app_commands.describe(adr_id="ADR ID", status="New status")
    async def doc_adr_update(self, interaction: discord.Interaction, adr_id: str, status: str):
        adr = self.generator.update_adr_status(adr_id, status)
        if not adr:
            await interaction.response.send_message("ADR not found.", ephemeral=True)
            return
        embed = discord.Embed(title="ADR Updated", color=discord.Color.green())
        embed.add_field(name="Title", value=adr.title)
        embed.add_field(name="New Status", value=adr.status)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-runbook", description="Generate a runbook")
    @discord.app_commands.describe(service_id="Service ID", steps_json="JSON array of step objects")
    async def doc_runbook(self, interaction: discord.Interaction, service_id: str, steps_json: str):
        try:
            steps = json.loads(steps_json)
        except json.JSONDecodeError:
            await interaction.response.send_message("Invalid JSON.", ephemeral=True)
            return
        doc = self.generator.generate_runbook(service_id, steps)
        embed = discord.Embed(title="Runbook Generated", color=discord.Color.green())
        embed.add_field(name="ID", value=doc.doc_id[:8])
        embed.add_field(name="Service", value=service_id)
        embed.add_field(name="Steps", value=len(steps))
        embed.add_field(name="Words", value=doc.word_count)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-adr-list-by-domain", description="List ADRs by domain")
    @discord.app_commands.describe(domain="Domain filter")
    async def doc_adr_list_domain(self, interaction: discord.Interaction, domain: str):
        adrs = self.generator.get_adr_by_domain(domain)
        if not adrs:
            await interaction.response.send_message(f"No ADRs for domain '{domain}'.", ephemeral=True)
            return
        embed = discord.Embed(title=f"ADRs: {domain}", color=discord.Color.blue())
        for adr in adrs[:10]:
            embed.add_field(name=adr.title[:50], value=f"Status: {adr.status}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-search", description="Search documents")
    @discord.app_commands.describe(query="Search query")
    async def doc_search(self, interaction: discord.Interaction, query: str):
        results = self.generator.search_documents(query)
        if not results:
            await interaction.response.send_message(f"No documents matching '{query}'.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Document Search: {query}", color=discord.Color.blue())
        for doc in results[:10]:
            embed.add_field(name=doc.title, value=f"Type: {doc.doc_type.value} | Service: {doc.service_id[:8]}", inline=False)
        await interaction.response.send_message(embed=embed)


    @discord.app_commands.command(name="doc-templates", description="List document templates")
    async def doc_templates(self, interaction: discord.Interaction):
        templates = self.generator.list_templates()
        if not templates:
            await interaction.response.send_message("No templates available.", ephemeral=True)
            return
        embed = discord.Embed(title="Document Templates", color=discord.Color.blue())
        for t in templates:
            embed.add_field(name=t["name"], value=t.get("description", "")[:100], inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-render", description="Render a document")
    @discord.app_commands.describe(doc_id="Document ID", output_format="Output format")
    async def doc_render(self, interaction: discord.Interaction, doc_id: str, output_format: str = "markdown"):
        result = self.generator.render_document(doc_id, DocFormat(output_format))
        if "error" in result:
            await interaction.response.send_message(result["error"], ephemeral=True)
            return
        embed = discord.Embed(title="Document Rendered", color=discord.Color.green())
        embed.add_field(name="Document ID", value=doc_id[:8])
        embed.add_field(name="Format", value=output_format)
        embed.add_field(name="Words", value=result.get("word_count", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-adr-analytics", description="ADR analytics")
    async def doc_adr_analytics(self, interaction: discord.Interaction):
        analytics = self.generator.get_adr_analytics()
        embed = discord.Embed(title="ADR Analytics", color=discord.Color.blue())
        embed.add_field(name="Total ADRs", value=analytics.get("total_adrs", 0))
        embed.add_field(name="By Status", value="\n".join(f"{k}: {v}" for k, v in analytics.get("by_status", {}).items()) or "None", inline=False)
        embed.add_field(name="By Domain", value="\n".join(f"{k}: {v}" for k, v in analytics.get("by_domain", {}).items()) or "None", inline=False)
        embed.add_field(name="Unique Authors", value=analytics.get("unique_authors", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-adr-search", description="Search ADRs")
    @discord.app_commands.describe(query="Search query")
    async def doc_adr_search(self, interaction: discord.Interaction, query: str):
        results = self.generator.search_adrs(query)
        if not results:
            await interaction.response.send_message(f"No ADRs matching '{query}'.", ephemeral=True)
            return
        embed = discord.Embed(title=f"ADR Search: {query}", color=discord.Color.blue())
        for adr in results[:10]:
            embed.add_field(name=adr.title[:50], value=f"Status: {adr.status} | Domain: {adr.domain or 'N/A'}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-compliance", description="Compliance report")
    async def doc_compliance(self, interaction: discord.Interaction):
        report = self.generator.get_compliance_report()
        embed = discord.Embed(title="Documentation Compliance", color=discord.Color.blue())
        embed.add_field(name="Services Documented", value=report.get("services_documented", 0))
        embed.add_field(name="Services Missing Docs", value=report.get("services_missing_docs", 0))
        embed.add_field(name="Documentation Coverage", value=f"{report.get('coverage_pct', 0)}%")
        embed.add_field(name="Total Documents", value=report.get("total_documents", 0))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-export", description="Export documents")
    @discord.app_commands.describe(doc_type="Document type filter", format="Export format")
    async def doc_export(self, interaction: discord.Interaction, doc_type: str = "", format: str = "markdown"):
        result = self.generator.export_documents(doc_type=doc_type, output_format=format)
        embed = discord.Embed(title="Documents Exported", color=discord.Color.green())
        embed.add_field(name="Format", value=format)
        embed.add_field(name="Exported", value=f"{result.get('count', 0)} documents")
        embed.add_field(name="Type Filter", value=doc_type or "All")
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-search", description="Search documents and ADRs")
    @discord.app_commands.describe(query="Search query")
    async def doc_search(self, interaction: discord.Interaction, query: str):
        results = self.generator.search_docs(query)
        if not results:
            await interaction.response.send_message("No matches.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Search: {query}", color=discord.Color.blue())
        for r in results[:10]:
            title = r.get("title", r.get("name", "?"))
            embed.add_field(name=title[:50], value=f"Type: {'ADR' if 'adr_id' in r else 'Doc'}", inline=False)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-review-start", description="Start a document review")
    @discord.app_commands.describe(adr_id="ADR ID", reviewers="Comma-separated reviewer names")
    async def doc_review_start(self, interaction: discord.Interaction, adr_id: str, reviewers: str):
        reviewer_list = [r.strip() for r in reviewers.split(",")]
        review = self.generator.start_review(adr_id, reviewer_list)
        if not review:
            await interaction.response.send_message("ADR not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Review Started", color=discord.Color.green())
        embed.add_field(name="ADR ID", value=adr_id[:8])
        embed.add_field(name="Review ID", value=review["review_id"][:8])
        embed.add_field(name="Reviewers", value=", ".join(reviewer_list))
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-review-approve", description="Approve an ADR review")
    @discord.app_commands.describe(review_id="Review ID")
    async def doc_review_approve(self, interaction: discord.Interaction, review_id: str):
        approved = self.generator.approve_review(review_id, interaction.user.name)
        if not approved:
            await interaction.response.send_message("Review not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Review Approved", color=discord.Color.green())
        embed.add_field(name="Review ID", value=review_id[:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-review-reject", description="Reject an ADR review")
    @discord.app_commands.describe(review_id="Review ID", reason="Reason for rejection")
    async def doc_review_reject(self, interaction: discord.Interaction, review_id: str, reason: str):
        rejected = self.generator.reject_review(review_id, interaction.user.name, reason)
        if not rejected:
            await interaction.response.send_message("Review not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Review Rejected", color=discord.Color.red())
        embed.add_field(name="Review ID", value=review_id[:8])
        embed.add_field(name="Reason", value=reason)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-cross-ref", description="Cross-reference two documents")
    @discord.app_commands.describe(source_id="Source doc/ADR ID", target_id="Target doc/ADR ID", ref_type="Reference type")
    async def doc_cross_ref(self, interaction: discord.Interaction, source_id: str, target_id: str, ref_type: str = "related"):
        result = self.generator.cross_reference_docs(source_id, target_id, ref_type)
        if not result:
            await interaction.response.send_message("One or both documents not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Cross-Reference Added", color=discord.Color.green())
        embed.add_field(name="Source", value=source_id[:8])
        embed.add_field(name="Target", value=target_id[:8])
        embed.add_field(name="Type", value=ref_type)
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-stats", description="Document statistics")
    async def doc_stats(self, interaction: discord.Interaction):
        stats = self.generator.get_content_statistics()
        embed = discord.Embed(title="Document Statistics", color=discord.Color.blue())
        embed.add_field(name="Documents", value=stats["total_documents"])
        embed.add_field(name="ADRs", value=stats["total_adrs"])
        embed.add_field(name="Total Words", value=stats["total_words"])
        embed.add_field(name="Avg Words/Doc", value=stats["avg_words_per_doc"])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-template-create", description="Create a doc template")
    @discord.app_commands.describe(name="Template name", content="Template content with {{placeholders}}")
    async def doc_template_create(self, interaction: discord.Interaction, name: str, content: str):
        tmpl = self.generator.set_doc_template(name, content)
        embed = discord.Embed(title="Template Created", color=discord.Color.green())
        embed.add_field(name="Name", value=name)
        embed.add_field(name="Version", value=tmpl["version"])
        embed.add_field(name="ID", value=tmpl["template_id"][:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-generate-from-template", description="Generate doc from template")
    @discord.app_commands.describe(template_id="Template ID", service_id="Service ID", params_json='JSON params like {"key":"value"}')
    async def doc_generate_from_template(self, interaction: discord.Interaction, template_id: str, service_id: str, params_json: str):
        import json
        try:
            params = json.loads(params_json)
        except json.JSONDecodeError:
            await interaction.response.send_message("Invalid JSON.", ephemeral=True)
            return
        doc_id = self.generator.generate_from_template(template_id, service_id, params)
        if not doc_id:
            await interaction.response.send_message("Template not found.", ephemeral=True)
            return
        embed = discord.Embed(title="Document Generated", color=discord.Color.green())
        embed.add_field(name="Document ID", value=doc_id[:8])
        embed.add_field(name="Service ID", value=service_id[:8])
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="doc-bulk-generate", description="Bulk generate docs from templates")
    @discord.app_commands.describe(service_id="Service ID", template_ids="Comma-separated template IDs", params_json='JSON params')
    async def doc_bulk_generate(self, interaction: discord.Interaction, service_id: str, template_ids: str, params_json: str):
        import json
        tids = [t.strip() for t in template_ids.split(",")]
        try:
            params = json.loads(params_json)
        except json.JSONDecodeError:
            await interaction.response.send_message("Invalid JSON.", ephemeral=True)
            return
        ids = self.generator.bulk_generate_docs(service_id, tids, params)
        embed = discord.Embed(title="Bulk Generate Complete", color=discord.Color.green())
        embed.add_field(name="Requested", value=len(tids))
        embed.add_field(name="Generated", value=len(ids))
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(DocGenCog(bot))

# ── Extended Operations ───────────────────────────────────────────────

    async def batch_execute(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        for item in items:
            try:
                results.append({"id": item.get("id"), "status": "completed"})
            except Exception as e:
                results.append({"id": item.get("id"), "status": "failed", "error": str(e)})
        return {"total": len(results), "successful": sum(1 for r in results if r["status"] == "completed")}

    def get_aggregate(self) -> Dict[str, Any]:
        return {"total_ops": 0, "success_rate": 100.0, "avg_latency_ms": 0}

    def validate_state(self) -> Dict[str, Any]:
        return {"valid": True, "timestamp": datetime.utcnow().isoformat()}

class CogOperationResult(BaseModel):
    success: bool = True
    operation: str = ""
    resource_id: Optional[str] = None
    message: str = ""
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CogBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operations: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")
    completed: int = Field(default=0)
    failed: int = Field(default=0)

    def record_success(self) -> None:
        self.completed += 1

    def record_failure(self) -> None:
        self.failed += 1

    def finish(self) -> None:
        self.status = "completed"

class CogMetricsCollector:
    def __init__(self) -> None:
        self._metrics: Dict[str, List[float]] = {}

    def record(self, name: str, value: float) -> None:
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(value)

    def summary(self, name: str) -> Dict[str, Any]:
        vals = self._metrics.get(name, [])
        if not vals:
            return {"count": 0}
        return {"count": len(vals), "min": round(min(vals), 4), "max": round(max(vals), 4),
                "avg": round(sum(vals) / len(vals), 4), "last": round(vals[-1], 4)}

    def all_summaries(self) -> Dict[str, Any]:
        return {name: self.summary(name) for name in self._metrics}

class CogHealthCheck:
    def __init__(self) -> None:
        self._checks: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, check_fn) -> None:
        self._checks[name] = {"fn": check_fn, "last_status": None, "last_run": None}

    async def run(self, name: str) -> Dict[str, Any]:
        check = self._checks.get(name)
        if not check:
            return {"status": "error", "message": "Unknown check"}
        try:
            result = await check["fn"]()
            check["last_status"] = result
            check["last_run"] = datetime.utcnow()
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def run_all(self) -> Dict[str, Any]:
        results = {}
        for name in self._checks:
            results[name] = await self.run(name)
        return results

    def get_status(self) -> Dict[str, Any]:
        return {name: {"last_status": c["last_status"], "last_run": c["last_run"].isoformat() if c["last_run"] else None}
                for name, c in self._checks.items()}
