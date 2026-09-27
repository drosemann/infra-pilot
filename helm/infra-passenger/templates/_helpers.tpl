{{/* vim: set filetype=helm: */}}
{{- define "infra-passenger.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "infra-passenger.fullname" -}}
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

{{- define "infra-passenger.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "infra-passenger.labels" -}}
helm.sh/chart: {{ include "infra-passenger.chart" . }}
{{ include "infra-passenger.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "infra-passenger.selectorLabels" -}}
app.kubernetes.io/name: {{ include "infra-passenger.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "infra-passenger.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "infra-passenger.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/* Stable secret name shared by chart-generated Secret and all consumers (postgresql, redis, deployment).
     Using a literal ensures values.yaml existingSecret (infra-passenger-secrets) and templates stay in sync regardless
     of Release.Name/fullnameOverride. For Bitnami Redis use existingSecretPasswordKey=redis-password (not secretKeys). */}}
{{- define "infra-passenger.secretName" -}}
infra-passenger-secrets
{{- end }}