{{/* vim: set filetype=helm: */}}
{{- define "infra-pilot.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "infra-pilot.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "infra-pilot.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "infra-pilot.labels" -}}
helm.sh/chart: {{ include "infra-pilot.chart" . }}
{{ include "infra-pilot.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "infra-pilot.selectorLabels" -}}
app.kubernetes.io/name: {{ include "infra-pilot.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "infra-pilot.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "infra-pilot.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/* Stable secret name shared by chart-generated Secret and all consumers (postgresql, redis, deployment).
     Using a literal ensures values.yaml existingSecret (infra-pilot-secrets) and templates stay in sync regardless
     of Release.Name/fullnameOverride. For Bitnami Redis use existingSecretPasswordKey=redis-password (not secretKeys). */}}
{{- define "infra-pilot.secretName" -}}
infra-pilot-secrets
{{- end }}

{{/* Look up the value of a named entry in a list of {name, value} env entries.
     Input: dict "name" <string> "env" <list>. Returns "" when absent so callers
     can chain `| default`. */}}
{{- define "infra-pilot.envValue" -}}
{{- $name := .name -}}
{{- $result := "" -}}
{{- range $entry := (.env | default list) -}}
{{- if eq (get $entry "name") $name -}}
{{- $result = (get $entry "value") -}}
{{- end -}}
{{- end -}}
{{- $result -}}
{{- end }}

{{/* Resolve the PostgreSQL host used by Jobs. Order: explicit override ->
     orchestrator DB_HOST env value -> "<release>-postgresql" (Bitnami default).
     Input: dict "root" . "explicit" <string>. */}}
{{- define "infra-pilot.pgHost" -}}
{{- $explicit := (get . "explicit") | default "" -}}
{{- if $explicit -}}
{{- $explicit -}}
{{- else -}}
{{- $fromEnv := include "infra-pilot.envValue" (dict "name" "DB_HOST" "env" .root.Values.orchestrator.env) -}}
{{- if $fromEnv -}}
{{- $fromEnv -}}
{{- else -}}
{{- printf "%s-postgresql" .root.Release.Name -}}
{{- end -}}
{{- end -}}
{{- end }}

{{/* Resolve a PostgreSQL connection detail (port/user/database) for Jobs.
     Order: explicit override -> matching DB_* orchestrator env value ->
     chart postgresql.auth.<key> (in-cluster Bitnami) -> supplied fallback.
     Input: dict "root" . "explicit" <string> "env" DB_PORT|DB_USER|DB_NAME
     "auth" postgresql.auth.<key> "fallback" <string> "quoted" <bool>. */}}
{{- define "infra-pilot.pgDetail" -}}
{{- $explicit := get . "explicit" | default "" -}}
{{- $fromEnv := include "infra-pilot.envValue" (dict "name" (get . "env") "env" .root.Values.orchestrator.env) -}}
{{- $fromAuth := "" -}}
{{- if .root.Values.postgresql.enabled -}}
{{- $fromAuth = (get (.root.Values.postgresql.auth | default dict) (get . "auth")) | default "" -}}
{{- end -}}
{{- $value := $explicit | default $fromEnv | default $fromAuth | default (get . "fallback") -}}
{{- if (get . "quoted") -}}
{{- $value | quote -}}
{{- else -}}
{{- $value -}}
{{- end -}}
{{- end }}

{{/* Helm hook events for the migration Job. Empty value = automatic:
     post-install,pre-upgrade when the database is created by this release or
     the credentials Secret is chart-managed (a pre-install hook runs before
     the Bitnami PostgreSQL resources and the chart Secret exist, which would
     deadlock), pre-install,pre-upgrade only when the database is external and
     the credentials Secret is external (secrets.create=false) so it already
     exists. */}}
{{- define "infra-pilot.migrationHookEvents" -}}
{{- $override := .Values.migration.hook.events | default "" -}}
  {{- if $override -}}
  {{- $override -}}
  {{- else if or .Values.postgresql.enabled .Values.secrets.create -}}
  post-install,pre-upgrade
  {{- else -}}
  pre-install,pre-upgrade
  {{- end -}}
{{- end }}

{{/* Name of the ServiceAccount created for Jobs (migration/backup/restore). */}}
{{- define "infra-pilot.jobsServiceAccount" -}}
{{- if .Values.jobs.serviceAccount.name -}}
{{- .Values.jobs.serviceAccount.name -}}
{{- else if .Values.jobs.serviceAccount.create -}}
{{- printf "%s-jobs" (include "infra-pilot.fullname" .) -}}
{{- else -}}
default
{{- end -}}
{{- end }}

{{/* ServiceAccount used by the migration hook Job. When the hook runs at
     pre-install time the release ServiceAccounts do not exist yet, so the
     namespace default ServiceAccount is used instead (it needs no RBAC). */}}
{{- define "infra-pilot.migrationServiceAccount" -}}
{{- if has "pre-install" (splitList "," (include "infra-pilot.migrationHookEvents" .)) -}}
{{- if and .Values.jobs.serviceAccount.create (not .Values.jobs.serviceAccount.name) -}}
default
{{- else -}}
{{- include "infra-pilot.jobsServiceAccount" . -}}
{{- end -}}
{{- else -}}
{{- include "infra-pilot.jobsServiceAccount" . -}}
{{- end -}}
{{- end }}

{{/* Container image used by the migration Job: explicit override, otherwise
     the orchestrator image (it ships Alembic and the alembic/ directory). */}}
{{- define "infra-pilot.migrationImage" -}}
{{- $repo := .Values.migration.image.repository | default .Values.orchestrator.image.repository -}}
{{- $tag := .Values.migration.image.tag | default .Values.orchestrator.image.tag | default .Chart.AppVersion -}}
{{- printf "%s:%s" $repo $tag -}}
{{- end }}