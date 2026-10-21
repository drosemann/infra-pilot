# Secrets backing (Vault / AWS Secrets Manager)

Concrete policy and IAM examples for the orchestrator's
`secrets_service.py` backends. The orchestrator needs only the minimum
listed below — it reads/writes/rotates KV entries it consumes itself; it
must never hold broad wildcards.

---

## Vault (KV v2)

Recommended auth: **AppRole** (`VAULT_ROLE_ID` + `VAULT_SECRET_ID`) rather
than a long-lived token. Enable `kv` (v2) and create a scoped policy:

```hcl
# vault: policy for the infra-pilot orchestrator
path "kv/data/infra-pilot/*" {
  capabilities = ["create", "read", "update"]
  # Mount versioning ("rotate") rewrites the highest version of a path;
  # delete is intentionally not granted — cleanup is an operator action.
}

path "auth/token/renew-self" {
  capabilities = ["update"]
}
path "auth/approle/login" {
  capabilities = ["update"]
}
```

Mount and grant (operator one-time):

```bash
vault secrets enable -path=kv kv-v2
vault policy write infra-pilot-orchestrator infra-pilot.hcl
vault auth enable approle
vault write auth/approle/role/infra-pilot \
    secret_id_ttl=24h token_ttl=1h token_renewable=true
vault read auth/approle/role/infra-pilot/role-id
vault write -f auth/approle/role/infra-pilot/secret-id
```

Secret path convention: `kv/data/infra-pilot/<org>/<app>/<name>`; panel
references use `vault://<path>#<key>`.

## AWS Secrets Manager

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InfraPilotSecretsScope",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:GetSecretString",
        "secretsmanager:PutSecretValue",
        "secretsmanager:CreateSecret",
        "secretsmanager:RotateSecret"
      ],
      "Resource": "arn:aws:secretsmanager:*:<account-id>:secret:infra-pilot/*"
    }
  ]
}
```

Attach the AWS access through an instance role / workload identity — do
not use a long-lived access key for the orchestrator.
`AWS_REGION` / `AWS_PROFILE` select the client; references use
`aws-sm://infra-pilot/<name>`.

## Panel ↔ orchestrator

The panel resolves references through `POST /api/v1/secrets/get` and
rotates through `POST /api/v1/secrets/rotate` using
`ORCHESTRATOR_API_TOKEN` (the federation credential) against
`ORCHESTRATOR_ORG_ID`. That org must exist in the orchestrator RBAC and
hold the `secret:*` permissions for the acting user.

## Optional dependencies

`hvac` (Vault) and `boto3` (AWS) are lazy optional dependencies in
`services/orchestrator-agent/requirements-optional.txt`; the orchestrator
starts without them and fails closed (`503`) when a backend is selected
but its client library is unavailable.
