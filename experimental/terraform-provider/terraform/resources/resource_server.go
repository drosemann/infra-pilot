package resources

import (
	"context"
	"fmt"

	"github.com/hashicorp/terraform-plugin-sdk/v2/diag"
	"github.com/hashicorp/terraform-plugin-sdk/v2/helper/schema"
	"github.com/hashicorp/terraform-plugin-sdk/v2/helper/validation"
)

func ResourceServer() *schema.Resource {
	return &schema.Resource{
		CreateContext: resourceServerCreate,
		ReadContext:   resourceServerRead,
		UpdateContext: resourceServerUpdate,
		DeleteContext: resourceServerDelete,
		Schema: map[string]*schema.Schema{
			"name": {
				Type:     schema.TypeString,
				Required: true,
				ForceNew: false,
			},
			"type": {
				Type:         schema.TypeString,
				Required:     true,
				ForceNew:     true,
				ValidateFunc: validation.StringInSlice([]string{"minecraft", "nodejs", "python", "database", "teamspeak"}, false),
			},
			"memory": {
				Type:     schema.TypeInt,
				Optional: true,
				Default:  1024,
			},
			"disk": {
				Type:     schema.TypeInt,
				Optional: true,
				Default:  1024,
			},
			"cpu": {
				Type:     schema.TypeInt,
				Optional: true,
				Default:  100,
			},
			"status": {
				Type:     schema.TypeString,
				Computed: true,
			},
			"identifier": {
				Type:     schema.TypeString,
				Computed: true,
			},
			"node_id": {
				Type:     schema.TypeInt,
				Optional: true,
				Computed: true,
			},
		},
		Importer: &schema.ResourceImporter{
			StateContext: schema.ImportStatePassthroughContext,
		},
	}
}

func resourceServerCreate(ctx context.Context, d *schema.ResourceData, m interface{}) diag.Diagnostics {
	config := m.(*struct{ APIURL, APIKey string })
	_ = config

	name := d.Get("name").(string)
	serverType := d.Get("type").(string)
	memory := d.Get("memory").(int)

	d.SetId(fmt.Sprintf("%s-%s", serverType, name))
	d.Set("identifier", d.Id())
	d.Set("status", "creating")

	return nil
}

func resourceServerRead(ctx context.Context, d *schema.ResourceData, m interface{}) diag.Diagnostics {
	return nil
}

func resourceServerUpdate(ctx context.Context, d *schema.ResourceData, m interface{}) diag.Diagnostics {
	return resourceServerRead(ctx, d, m)
}

func resourceServerDelete(ctx context.Context, d *schema.ResourceData, m interface{}) diag.Diagnostics {
	d.SetId("")
	return nil
}
