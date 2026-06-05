# Feature 32: Internal Knowledge Base

- **Feature ID:** 32
- **Status:** Planned
- **Priority:** Medium
- **Primary Service:** Management Panel
- **Effort:** Medium (4–6 PT)

---

## 1. Overview

The Internal Knowledge Base (KB) provides a Markdown-based wiki tightly integrated with the infra-pilot resource model. Operators can author and organize documentation, link articles directly to servers, clusters, runbooks, or alerts, and automatically generate reference docs from live server configurations. Full-text search across all articles, categories for navigation, and version history for every document ensure the KB stays the single source of truth for operational knowledge.

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Management Panel                        │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │ Markdown    │  │ Resource     │  │ Auto-Gen       │   │
│  │ Editor      │  │ Linker       │  │ Docs Engine    │   │
│  │ (CodeMirror)│  │ (tag/ID      │  │ (config → md)  │   │
│  └──────┬──────┘  │  picker)     │  └───────┬────────┘   │
│         │         └──────┬───────┘          │            │
│         ▼                ▼                  ▼            │
│  ┌──────────────────────────────────────────────────┐    │
│  │            Knowledge Base API (REST)              │    │
│  └──────────────────────┬───────────────────────────┘    │
└─────────────────────────┼───────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                   Knowledge Base Service                  │
│                                                           │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐    │
│  │ Article    │  │ Category   │  │ Search Index     │    │
│  │ Store      │  │ Store      │  │ (Bleve / Meilisearch) │
│  ├────────────┤  ├────────────┤  ├──────────────────┤    │
│  │ Version    │  │ Resource   │  │ Auto-Gen Config  │    │
│  │ History    │  │ Link Index │  │ Templates        │    │
│  └────────────┘  └────────────┘  └──────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

**Components:**

| Component | Role |
|---|---|
| Markdown Editor | WYSIWYM editing experience with preview pane, syntax highlighting, image upload |
| Resource Linker | Manages bidirectional links between KB articles and infrastructure resources |
| Auto-Gen Docs Engine | Renders live server/config data into read-only Markdown articles using templates |
| Search Index | Full-text engine with tagging, faceted filtering, and relevance scoring |
| Version History | Immutable snapshots of every article on save; diff viewer for rollback |

---

## 3. API Design

### 3.1 Articles

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/kb/articles` | List articles (paginated, filterable by category / tag / resource) |
| `POST` | `/api/v1/kb/articles` | Create article |
| `GET` | `/api/v1/kb/articles/{id}` | Get article (latest version by default) |
| `PUT` | `/api/v1/kb/articles/{id}` | Update article (creates new version) |
| `DELETE` | `/api/v1/kb/articles/{id}` | Soft-delete article |
| `GET` | `/api/v1/kb/articles/{id}/versions` | List version history |
| `GET` | `/api/v1/kb/articles/{id}/versions/{v}` | Get specific version |
| `POST` | `/api/v1/kb/articles/{id}/restore/{v}` | Restore a previous version |

### 3.2 Categories

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/kb/categories` | List categories (tree structure) |
| `POST` | `/api/v1/kb/categories` | Create category |
| `PUT` | `/api/v1/kb/categories/{id}` | Rename / move category |
| `DELETE` | `/api/v1/kb/categories/{id}` | Delete category (optionally cascade) |

### 3.3 Search

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/kb/search?q={query}&category={id}&tag={t}` | Full-text search across articles |

### 3.4 Auto-Generated Docs

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/kb/autogen/{resource_type}/{id}` | Generate or regenerate auto-doc for a resource |
| `GET` | `/api/v1/kb/autogen/{resource_type}/{id}` | Get the generated doc (read-only article) |
| `GET` | `/api/v1/kb/autogen/templates` | List available auto-gen templates |
| `PUT` | `/api/v1/kb/autogen/templates/{name}` | Customise an auto-gen template |

---

## 4. Data Model

```json
{
  "article": {
    "id": "uuid",
    "title": "string",
    "slug": "postgres-failover-procedure",
    "body_markdown": "string (Markdown content)",
    "category_id": "uuid",
    "tags": ["postgres", "recovery", "runbook"],
    "linked_resources": [
      {"type": "server", "id": "srv-abc-123"},
      {"type": "runbook", "id": "rb-xyz-456"}
    ],
    "auto_generated": false,
    "auto_gen_source": {"resource_type": "server", "resource_id": "srv-abc-123", "template": "server-config.md.tmpl"},
    "author_id": "uuid",
    "version": 12,
    "created_at": "rfc3339",
    "updated_at": "rfc3339"
  },

  "article_version": {
    "id": "uuid",
    "article_id": "uuid",
    "version_number": 12,
    "body_markdown": "string",
    "diff_from_previous": "string (unified diff)",
    "author_id": "uuid",
    "created_at": "rfc3339"
  },

  "category": {
    "id": "uuid",
    "name": "Database Operations",
    "description": "Runbooks and guides for database administration",
    "parent_id": "uuid (null for root)",
    "article_count": 15,
    "created_at": "rfc3339"
  }
}
```

---

## 5. Auto-Generated Documentation

When a server or resource is created/updated, the system can render a read-only Markdown article from a Go template. Example template `server-config.md.tmpl`:

```markdown
# {{ .Resource.Name }} — Configuration Reference

- **Type:** {{ .Resource.Type }}
- **Host:** `{{ .Resource.Hostname }}`
- **IP:** {{ .Resource.IP }}
- **OS:** {{ .Resource.OS }} {{ .Resource.OSVersion }}
- **Created:** {{ .Resource.CreatedAt | date "2006-01-02" }}
- **Tags:** {{ join .Resource.Tags ", " }}

## Installed Services

| Service | Version | Port | Status |
|---------|---------|------|--------|
{{- range .Resource.Services }}
| {{ .Name }} | {{ .Version }} | {{ .Port }} | {{ .Status }} |
{{- end }}

## Environment Variables

| Variable | Value |
|----------|-------|
{{- range $k, $v := .Resource.Env }}
| {{ $k }} | `{{ $v }}` |
{{- end }}

## Linked Runbooks

{{- range .Resource.LinkedRunbooks }}
- [{{ .Name }}](/kb/runbook/{{ .ID }})
{{- end }}

---

*This document is auto-generated. Manual edits will be overwritten on next sync.*
```

---

## 6. Resource Linking

Bidirectional links are stored in a dedicated join table:

```sql
CREATE TABLE kb_resource_links (
    id            UUID PRIMARY KEY,
    article_id    UUID NOT NULL REFERENCES kb_articles(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,   -- 'server', 'runbook', 'alert', 'dashboard'
    resource_id   VARCHAR(255) NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(article_id, resource_type, resource_id)
);

CREATE INDEX idx_kb_links_resource
    ON kb_resource_links(resource_type, resource_id);
```

When viewing a resource detail page, the Management Panel queries this index to show "Linked KB Articles" and "Auto-Generated Docs".

---

## 7. Search

| Aspect | Implementation |
|---|---|
| Engine | Bleve (embedded Go) or Meilisearch (external, recommended for scale) |
| Indexed fields | `title`, `body_markdown`, `tags`, `category_name`, `linked_resource_names` |
| Filters | Category, tag, resource type, auto-gen flag, author, date range |
| Ranking | TF-IDF with recency boost; exact phrase matches ranked highest |
| Query syntax | Full-text keywords; quoted phrases; `tag:postgres` scoping; `author:alice` |

---

## 8. Service Assignments

| Service | Responsibilities |
|---|---|
| **Management Panel** | Markdown editor, resource link picker, category tree, search UI, auto-gen doc viewer |
| **Knowledge Base Service** | Articles CRUD, versioning engine, search indexing, auto-gen rendering, resource link resolver |
| **Event Store** | Publish article created/updated/deleted events for search re-index |
| **Identity & Access** | Restrict write access; article-level ACLs (owner-editor-viewer) |

---

## 9. Effort Estimate

| Phase | Tasks | PT |
|---|---|---|
| Design | API contracts, data model, search schema, template format | 0.5 |
| Backend CRUD | Articles, categories, versions, resource links | 1 |
| Search | Index engine integration, query API, faceted filters | 1 |
| Auto-Gen Engine | Template rendering, resource-to-doc mapping, regeneration triggers | 0.5 |
| Markdown Editor | CodeMirror integration, preview pane, image upload | 1 |
| Resource Linker UI | Resource picker component, linked-article panel on resource pages | 0.5 |
| Testing & Docs | Integration tests, template examples, user guide | 0.5 |
| **Total** | | **4–6** |

---

## 10. Future Considerations

- **Commenting / feedback**: Allow inline comments on articles
- **Export**: Whole-KB export to static HTML or PDF
- **Webhook triggers**: Re-generate auto-docs when resources change
- **Cross-KB links**: `[[article:slug]]` syntax in Markdown for internal linking
- **AI assistant**: Q&A bot trained on KB content for natural-language queries
