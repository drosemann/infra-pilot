# Why we touch every pod personally

A pilot tries to make the route disappear behind automation. A passenger in
infra-passenger sits in the backseat with the map open, asks where the route
goes, and can still point at every pod personally.

That is the joke and the operating model. We use health checks, GitOps,
metrics, and scripts, but we do not call an opaque default “control.” The
person responsible can inspect logs, view the manifest, run the command, and
understand the consequence before a change reaches production.

This is Hanau FISI second-year energy: funny because it is true, solid because
it has to work on Monday. No corporate magic, no poverty theatre—just the
Mitte between hands-off autopilot and manually rebuilding the whole cluster.
