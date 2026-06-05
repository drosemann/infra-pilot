# feature 35: custom dashboard builder

- feature id: 35
- status: planned
- priority: medium
- primary service: management panel
- effort: extra large (11+ pt)

## overview

the custom dashboard builder is a drag-and-drop visual editor that enables operators to compose real-time operational dashboards without writing code. inspired by grafana, it supports multiple panel types (time-series graphs, stat singletons, log viewers, alert lists), configurable data source queries, dashboard sharing and templating. dashboards are persisted as json definitions and rendered entirely on the management panel front-end with data fetched through a unified query proxy.

## architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Management Panel (Browser)                   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                 Dashboard Builder (React)                   │   │
│  │                                                             │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │   │
│  │  │ Canvas     │  │ Panel      │  │ Query Editor      │    │   │
│  │  │ (react-   │  │ Library    │  │ (SQL / PromQL /    │    │   │
│  │  │  grid-    │  │ (drag into │  │  LogQL builders)   │    │   │
│  │  │  layout)  │  │  canvas)   │  └────────────────────┘    │   │
│  │  └────────────┘  └────────────┘                             │   │
│  │  ┌────────────┐  ┌──────────────────────────────────────┐  │   │
│  │  │ Panel      │  │ Data Source Selector                 │  │   │
│  │  │ Renderer   │  │ (Prometheus, Loki, PostgreSQL,       │  │   │
│  │  │ (ECharts / │  │  InfluxDB, OpenTSDB, + custom)      │  │   │
│  │  │  uPlot)    │  └──────────────────────────────────────┘  │   │
│  │  └────────────┘                                             │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │              Dashboard API Client (REST)                    │   │
│  └─────────────────────────┬─────────────────────────────────┘   │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                  Management Panel Backend                         │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐   │
│  │ Dashboard CRUD   │  │ Dashboard Share  │  │ Template      │   │
│  │ + Versioning     │  │ (link / embed /  │  │ Engine        │   │
│  │                  │  │  RBAC)           │  │ (variables →  │   │
│  └────────┬─────────┘  └──────────────────┘  │  interpolation│   │
│           │                                   └───────┬───────┘   │
│           ▼                                           ▼           │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                Query Proxy Service                          │   │
│  │                                                             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │Prometheus│  │  Loki    │  │PostgreSQL│  │ InfluxDB │    │   │
│  │  │ Querier  │  │  Querier │  │ Querier  │  │ Querier  │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

## dashboard json schema

dashboards are stored as json and versioned. every mutation creates a new version.

```json
{
  "dashboard": {
    "id": "dash_abc123",
    "title": "Postgres Cluster Overview",
    "description": "Key health metrics for the Postgres primary-replica cluster",
    "tags": ["postgres", "database", "production"],
    "templating": {
      "variables": [
        {
          "name": "cluster",
          "type": "query",
          "query": "label_values(pg_up, cluster)",
          "include_all": true,
          "multi": true,
          "refresh": "on_dashboard_load"
        },
        {
          "name": "instance",
          "type": "query",
          "query": "label_values(pg_up{cluster=\"$cluster\"}, instance)",
          "include_all": false,
          "multi": false
        }
      ]
    },
    "panels": [
      {
        "id": "panel_001",
        "type": "timeseries",
        "title": "Connections",
        "description": "Active database connections over time",
        "grid": {
          "x": 0,
          "y": 0,
          "w": 12,
          "h": 6
        },
        "datasource": {
          "type": "prometheus",
          "uid": "prom_prod"
        },
        "targets": [
          {
            "expr": "sum(pg_stat_activity_count{cluster=\"$cluster\", instance=\"$instance\"}) by (state)",
            "legend_format": "{{ state }}",
            "resolution": "auto"
          }
        ],
        "options": {
          "line_interpolation": "smooth",
          "fill_opacity": 20,
          "stack": true,
          "thresholds": [
            {"value": 80, "color": "orange"},
            {"value": 120, "color": "red"}
          ]
        }
      },
      {
        "id": "panel_002",
        "type": "stat",
        "title": "Replication Lag",
        "grid": {
          "x": 12,
          "y": 0,
          "w": 6,
          "h": 3
        },
        "datasource": {
          "type": "prometheus",
          "uid": "prom_prod"
        },
        "targets": [
          {
            "expr": "max(pg_replication_lag{cluster=\"$cluster\"})",
            "legend_format": "max lag"
          }
        ],
        "options": {
          "unit": "bytes",
          "color_mode": "background",
          "thresholds": [
            {"value": 10485760, "color": "yellow"},
            {"value": 104857600, "color": "red"}
          ],
          "sparkline": {"show": true, "fill": true}
        }
      },
      {
        "id": "panel_003",
        "type": "log",
        "title": "Postgres Error Logs",
        "grid": {
          "x": 12,
          "y": 3,
          "w": 12,
          "h": 6
        },
        "datasource": {
          "type": "loki",
          "uid": "loki_prod"
        },
        "targets": [
          {
            "expr": "{cluster=\"$cluster\", service=\"postgres\"} |= \"ERROR\"",
            "max_lines": 500
          }
        ],
        "options": {
          "show_time": true,
          "wrap_lines": false,
          "prettify_json": true
        }
      },
      {
        "id": "panel_004",
        "type": "alert_list",
        "title": "Active Alerts",
        "grid": {
          "x": 0,
          "y": 6,
          "w": 12,
          "h": 4
        },
        "datasource": {
          "type": "prometheus",
          "uid": "prom_prod"
        },
        "targets": [
          {
            "expr": "ALERTS{alertstate=\"firing\", cluster=\"$cluster\"}"
          }
        ],
        "options": {
          "max_alerts": 50,
          "group_by": "severity",
          "show_details": true
        }
      }
    ],
    "time": {
      "from": "now-6h",
      "to": "now"
    },
    "refresh_interval": "30s",
    "editable": true,
    "shared_with": [
      {"type": "team", "id": "team_platform", "role": "viewer"},
      {"type": "user", "id": "usr_alice", "role": "editor"}
    ],
    "created_by": "usr_bob",
    "version": 7,
    "created_at": "2026-05-01T10:00:00Z",
    "updated_at": "2026-05-27T14:30:00Z"
  }
}
```

## panel types

| type | renderer | data source | options |
|---|---|---|---|
| timeseries | uPlot / ECharts | Prometheus, InfluxDB, PostgreSQL | Line interpolation, fill opacity, stack mode, thresholds, axis units, legend |
| stat | React + SVG | Prometheus, InfluxDB | Unit, color mode (text/background), thresholds, sparkline, value mapping |
| log | React (virtual scroll) | Loki, Elasticsearch | Show/hide time, wrap lines, prettify JSON, search highlight |
| alert_list | React table | Prometheus (ALERTS), Alertmanager API | Max items, group by severity, show labels, silence/acknowledge actions |
| table | React Table | PostgreSQL, Prometheus (instant) | Column sorting, column reorder, cell formatting |
| bar_chart | ECharts | Prometheus, InfluxDB | Orientation, grouping, color palette |
| heatmap | ECharts | Prometheus (histogram_quantile) | Bucket bound display, color scale |
| pie_chart | ECharts | Prometheus, InfluxDB | Label position, value mode (count/percentage) |
| text | Markdown / HTML | — (static content) | Content, mode (raw HTML / Markdown) |

## data source abstraction

the query proxy service translates a unified query request into backend-specific queries:

```json
// Unified query request (POST /api/v1/dashboards/query)
{
  "dashboard_id": "dash_abc123",
  "panel_id": "panel_001",
  "datasource": {"type": "prometheus", "uid": "prom_prod"},
  "targets": [
    {"expr": "sum(pg_stat_activity_count) by (state)", "legend_format": "{{ state }}"}
  ],
  "time": {"from": "2026-05-27T08:00:00Z", "to": "2026-05-27T14:00:00Z"},
  "resolution": "auto",
  "variables": {"cluster": "prod-us-east", "instance": "pg-1"}
}

// Unified query response
{
  "results": [
    {
      "target": "active",
      "datapoints": [
        [45.0, 1716800400],
        [47.0, 1716800430],
        ...
      ],
      "metadata": {"unit": "short"}
    }
  ]
}
```

## api design

### dashboard crud

| method | path | description |
|---|---|---|
| `GET` | `/api/v1/dashboards` | List dashboards (filterable by tag, owner) |
| `POST` | `/api/v1/dashboards` | Create dashboard |
| `GET` | `/api/v1/dashboards/{id}` | Get dashboard definition (latest version) |
| `PUT` | `/api/v1/dashboards/{id}` | Update dashboard (creates new version) |
| `DELETE` | `/api/v1/dashboards/{id}` | Soft-delete dashboard |
| `POST` | `/api/v1/dashboards/{id}/fork` | Fork (clone as new dashboard) |

### dashboard versioning

| method | path | description |
|---|---|---|
| `GET` | `/api/v1/dashboards/{id}/versions` | List version history |
| `GET` | `/api/v1/dashboards/{id}/versions/{v}` | Get specific version |
| `POST` | `/api/v1/dashboards/{id}/restore/{v}` | Restore a previous version |
| `GET` | `/api/v1/dashboards/{id}/diff/{v1}...{v2}` | Get diff between two versions |

### sharing & permissions

| method | path | description |
|---|---|---|
| `POST` | `/api/v1/dashboards/{id}/share` | Generate share link (optionally with expiry, password) |
| `DELETE` | `/api/v1/dashboards/{id}/share/{share_id}` | Revoke share link |
| `GET` | `/api/v1/dashboards/{id}/permissions` | Get access control list |
| `PUT` | `/api/v1/dashboards/{id}/permissions` | Set access control list |

### query execution

| method | path | description |
|---|---|---|
| `POST` | `/api/v1/dashboards/query` | Execute a unified query against a data source |
| `GET` | `/api/v1/dashboards/datasources` | List configured data sources and their health |
| `GET` | `/api/v1/dashboards/datasources/{uid}/types` | Get supported query types / metadata for a data source |

### templating

| method | path | description |
|---|---|---|
| `POST` | `/api/v1/dashboards/variable-query` | Execute a variable query (e.g. label_values) and return options |

## drag-and-drop canvas

the canvas is built on `react-grid-layout` with the following behaviours:

- grid: 24-column responsive layout, 30px row height unit
- resize: drag from bottom-right corner; min (4, 2), max (24, 20) grid units
- move: drag panel header; auto-reflow sibling panels
- add: drag panel type from panel library into canvas; opens query editor on drop
- duplicate: `ctrl+d` or context menu — copies panel with all settings
- remove: context menu or `delete` key — removes panel, reflows grid
- undo/redo: full history stack for all canvas mutations

```
┌──────────────────────────────────────────────────────────────────────┐
│  Dashboard: Postgres Cluster Overview              [Edit] [Save] [▶] │
│  ┌───────────┬───────────┬───────────┬───────────┬───────────┬────┐ │
│  │ Panel     │  + Add    │  Layout   │  Time:    │  Refresh  │ ⚙ │ │
│  │ Library   │   Panel   │  Tools    │  Last 6h  │  30s      │    │ │
│  └───────────┴───────────┴───────────┴───────────┴───────────┴────┘ │
│                                                                       │
│  ┌─────────────────────────────────────────┬──────────────────────┐   │
│  │  Connections (time-series)              │  Replication Lag     │   │
│  │  ┌──────────────────────────────────┐   │  ┌────────────────┐  │   │
│  │  │ ▁▃▅▇▆▅▃▂▁▃▅▇▆▅▃▂▁               │   │  │   42 MB        │  │   │
│  │  │ active: 45 ── idle: 12 ──        │   │  │   ▁▃▅▇▆▅▃▂▁     │  │   │
│  │  └──────────────────────────────────┘   │  └────────────────┘  │   │
│  └─────────────────────────────────────────┴──────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Active Alerts                                                   │ │
│  │  ┌──────┬──────────────┬────────┬──────────┬──────────────────┐ │ │
│  │  │ Sev  │ Alert        │ Host   │ Value    │ Since            │ │ │
│  │  ├──────┼──────────────┼────────┼──────────┼──────────────────┤ │ │
│  │  │ CRIT │ Disk >90%    │ pg-1   │ 94%      │ 2026-05-27 14:00 │ │ │
│  │  │ WARN │ Connections  │ pg-1   │ 110      │ 2026-05-27 13:45 │ │ │
│  │  └──────┴──────────────┴────────┴──────────┴──────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────┬──────────────────────┐   │
│  │  Postgres Error Logs                    │  Transactions (bar)  │   │
│  │  2026-05-27 14:01:23 ERROR: …           │  ┌──────────────┐    │   │
│  │  2026-05-27 14:00:57 ERROR: …           │  │ ██▄▇█▅▃▄▇██   │    │   │
│  └─────────────────────────────────────────┴──────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

## templating system

dashboard variables allow dynamic filtering without editing panels. variable types:

| type | description | example query |
|---|---|---|
| `query` | Value list from a data source query | `label_values(pg_up, cluster)` |
| `constant` | Single static value | `prod-us-east` |
| `custom` | Comma-separated user-defined list | `us-east, us-west, eu-west` |
| `interval` | Time range presets | `1m, 5m, 15m, 30m, 1h, 6h, 12h, 1d` |
| `textbox` | Free-form text input | `(user types a hostname)` |

variables are referenced in query expressions using `$variable` or `{{ variable }}` syntax.

## data model

```json
{
  "dashboard": {
    "id": "uuid",
    "title": "string",
    "description": "string",
    "tags": ["string"],
    "panels": [{"panel object as defined above"}],
    "templating": {"variables": [{"name": "string", "type": "string", "query": "string"}]},
    "time": {"from": "string", "to": "string"},
    "refresh_interval": "string",
    "editable": true,
    "shared_with": [{"type": "team|user", "id": "uuid", "role": "viewer|editor"}],
    "created_by": "uuid",
    "version": 7,
    "created_at": "rfc3339",
    "updated_at": "rfc3339"
  },

  "dashboard_version": {
    "id": "uuid",
    "dashboard_id": "uuid",
    "version_number": 7,
    "definition": {"full dashboard JSON"},
    "diff_from_previous": "string (JSON patch)",
    "author_id": "uuid",
    "created_at": "rfc3339"
  },

  "datasource": {
    "uid": "prom_prod",
    "type": "prometheus|loki|postgresql|influxdb",
    "name": "Prometheus Production",
    "url": "http://prometheus:9090",
    "access": "proxy|direct",
    "is_default": false,
    "secure_json_fields": {"auth_token": "encrypted"},
    "created_at": "rfc3339"
  }
}
```

## service assignments

| service | responsibilities |
|---|---|
| management panel (front-end) | drag-and-drop canvas (react-grid-layout), panel library, per-panel renderers (uPlot, ECharts, React Table), query editor, variable editor, dashboard share dialog |
| management panel (back-end) | dashboard crud, versioning, permissions, share link generation, variable query resolution |
| query proxy service | unified query endpoint, per-datasource querier adapters, time-series normalization, result caching |
| integration service | health-check endpoint for each data source |
| identity & access | dashboard-level rbac (viewer/editor/admin), share link authentication |

## effort estimate

| phase | tasks | pt |
|---|---|---|
| design | dashboard json schema, panel type spec, datasource adapter interface, wireframes | 1 |
| canvas & drag-drop | react-grid-layout integration, panel resize/move, add/remove/reorder, undo/redo | 2 |
| panel renderers | uPlot for time-series, stat panel, table, bar chart, heatmap (with ECharts), log viewer (virtual scroll), alert list | 3 |
| query editor | datasource selector, query builder ui, variable interpolation, preview | 1 |
| query proxy | datasource adapter framework, promql querier, logql querier, sql querier, result normalization, caching | 1.5 |
| versioning & diff | immutable version storage, restore, json-patch diff endpoint | 0.5 |
| sharing & rbac | share link generation (token-based), acl crud, permission checks | 0.5 |
| templating | variable engine, query-backed variable resolution, `$var` interpolation middleware | 1 |
| testing & polish | e2e tests (cypress) for drag-drop, panel rendering, datasource queries; performance tuning | 1 |
| documentation | user guide with screenshot gallery, datasource setup guide, api reference | 0.5 |
| total | | **11+** |

## data sources (initial release)

| datasource | type | query language | supported panel types |
|---|---|---|---|
| prometheus | `prometheus` | promql | timeseries, stat, bar_chart, heatmap, alert_list |
| loki | `loki` | logql | log, timeseries (metric queries) |
| postgresql | `postgresql` | sql | table, timeseries, stat, bar_chart |
| influxdb | `influxdb` | flux / influxql | timeseries, stat, bar_chart |
| opentsdb | `opentsdb` | opentsdb query | timeseries |
| json api | `json` | jsonpath | table, stat |
| elasticsearch | `elasticsearch` | query dsl | log, table, timeseries |

## future considerations

- annotations: overlay events (deployments, alerts) on time-series panels
- alerting from dashboards: one-click creation of alert rules from panel thresholds
- public dashboards: share dashboards with password protection and no auth required
- export / import: json export/import for dashboard migration between instances
- plugins: community datasource and panel plugin sdk
- ai-assisted panel generation: natural language → promql query generation
