# terraform provider for infra pilot

the infra pilot terraform provider allows you to manage infrastructure resources
such as servers, databases, and dns records through the infra pilot api.

## requirements

• [terraform](https://www.terraform.io/downloads) >= 1.0
• [go](https://golang.org/doc/install) >= 1.21 (to build the provider)
• infra pilot api access

## usage

```hcl
terraform {
  required_providers {
    infrapilot = {
      source = "infra-pilot/terraform-provider-infrapilot"
    }
  }
}

provider "infrapilot" {
  api_url = var.api_url
  api_key = var.api_key
}
```

## resources

• `infrapilot_server` - manage game and application servers
• `infrapilot_database` - manage mysql/postgresql databases
• `infrapilot_dns` - manage dns records

## data sources

• `infrapilot_server` - query existing server information

## authentication

authentication is handled via api key, which can be provided through the
`api_key` provider argument or the `ipilot_api_key` environment variable.
