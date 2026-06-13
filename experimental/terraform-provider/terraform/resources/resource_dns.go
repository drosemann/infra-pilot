package resources

import (
	"context"
	"fmt"

	"github.com/hashicorp/terraform-plugin-sdk/v2/diag"
	"github.com/hashicorp/terraform-plugin-sdk/v2/helper/schema"
	"github.com/hashicorp/terraform-plugin-sdk/v2/helper/validation"
)

func ResourceDNS() *schema.Resource {
	return &schema.Resource{
		CreateContext: resourceDNSCreate,
		ReadContext:   resourceDNSRead,
		UpdateContext: resourceDNSUpdate,
		DeleteContext: resourceDNSDelete,
		Schema: map[string]*schema.Schema{
			"zone": {
				Type:     schema.TypeString,
				Required: true,
				ForceNew: true,
			},
			"name": {
				Type:     schema.TypeString,
				Required: true,
				ForceNew: true,
			},
			"type": {
				Type:         schema.TypeString,
				Required:     true,
				ForceNew:     true,
				ValidateFunc: validation.StringInSlice([]string{"A", "AAAA", "CNAME", "MX", "TXT", "SRV", "NS"}, false),
			},
			"value": {
				Type:     schema.TypeString,
				Required: true,
			},
			"ttl": {
				Type:     schema.TypeInt,
				Optional: true,
				Default:  300,
			},
			"priority": {
				Type:     schema.TypeInt,
				Optional: true,
				Default:  0,
			},
			"proxied": {
				Type:     schema.TypeBool,
				Optional: true,
				Default:  false,
			},
		},
	}
}

func resourceDNSCreate(ctx context.Context, d *schema.ResourceData, m interface{}) diag.Diagnostics {
	zone := d.Get("zone").(string)
	name := d.Get("name").(string)
	recordType := d.Get("type").(string)

	d.SetId(fmt.Sprintf("%s_%s_%s", zone, name, recordType))
	return nil
}

func resourceDNSRead(ctx context.Context, d *schema.ResourceData, m interface{}) diag.Diagnostics {
	return nil
}

func resourceDNSUpdate(ctx context.Context, d *schema.ResourceData, m interface{}) diag.Diagnostics {
	return resourceDNSRead(ctx, d, m)
}

func resourceDNSDelete(ctx context.Context, d *schema.ResourceData, m interface{}) diag.Diagnostics {
	d.SetId("")
	return nil
}
