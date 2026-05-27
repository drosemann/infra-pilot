# infrapilot_server

manages a server instance through the infra pilot platform.

## example usage

```hcl
resource "infrapilot_server" "minecraft" {
  name   = "my-minecraft-server"
  type   = "minecraft"
  memory = 2048
  disk   = 4096
  cpu    = 200
}

resource "infrapilot_server" "node_app" {
  name   = "my-node-app"
  type   = "nodejs"
  memory = 512
}
```

## argument reference

• `name` - (required) the display name of the server.
• `type` - (required) the server type. must be one of: `minecraft`, `nodejs`,
  `python`, `database`, `teamspeak`.
• `memory` - (optional) memory allocation in mb. defaults to `1024`.
• `disk` - (optional) disk space allocation in mb. defaults to `1024`.
• `cpu` - (optional) cpu limit percentage. defaults to `100`.

## attributes reference

• `identifier` - the unique server identifier assigned by the api.
• `status` - the current status of the server (creating, active, stopping, etc.).
• `node_id` - the node id where the server is deployed.

## import

servers can be imported using the server identifier:

```shell
terraform import infrapilot_server.minecraft mc-abc123
```
