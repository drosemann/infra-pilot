package provider

import (
	"context"

	"github.com/hashicorp/terraform-plugin-sdk/v2/diag"
	"github.com/hashicorp/terraform-plugin-sdk/v2/helper/schema"
	"github.com/infra-pilot/terraform-provider-infrapilot/resources"
)

func Provider() *schema.Provider {
	return &schema.Provider{
		Schema: map[string]*schema.Schema{
			"api_url": {
				Type:        schema.TypeString,
				Required:    true,
				DefaultFunc: schema.EnvDefaultFunc("IPILOT_API_URL", "http://localhost:8080"),
				Description: "Infra Pilot API URL",
			},
			"api_key": {
				Type:        schema.TypeString,
				Required:    true,
				DefaultFunc: schema.EnvDefaultFunc("IPILOT_API_KEY", nil),
				Description: "API key for authentication",
				Sensitive:   true,
			},
		},
		ResourcesMap: map[string]*schema.Resource{
			"infrapilot_server":   resources.ResourceServer(),
			"infrapilot_database": resources.ResourceDatabase(),
			"infrapilot_dns":      resources.ResourceDNS(),
		},
		DataSourcesMap: map[string]*schema.Resource{
			"infrapilot_server": resources.DataSourceServer(),
		},
		ConfigureContextFunc: providerConfigure,
	}
}

type ProviderConfig struct {
	APIURL string
	APIKey string
}

func providerConfigure(ctx context.Context, d *schema.ResourceData) (interface{}, diag.Diagnostics) {
	config := &ProviderConfig{
		APIURL: d.Get("api_url").(string),
		APIKey: d.Get("api_key").(string),
	}
	return config, nil
}
