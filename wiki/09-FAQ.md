# FAQ

**What is infra-passenger?**
A tool that runs your apps and servers. You use it from the command line, a web page, or Discord.

**Why not just Terraform or Pulumi?**
infra-passenger works on top of them. It adds AI features, Discord control, energy tracking, and a web interface.

**I get "Connection failed" on `infra-passenger doctor doctor`?**
Check `docker compose ps`. Set the correct URL: `export INFRA_PASSENGER_API_URL=http://localhost:3001`.

**Can I run just some services?**
Yes. `docker compose up -d postgres redis`.

**How do I change the output format?**
`export INFRA_PASSENGER_OUTPUT=json` (or `infra-passenger --output json <command>`).

**200+ commands — how do I remember them?**
Use `infra-passenger --help` for the main list. Use `infra-passenger <command> --help` for details.

**Can I work offline?**
Yes. Use a local AI (Ollama, LM Studio). Set `AI_API_ENDPOINT` in `.env`.

---

*[Issues](https://github.com/drosemann/infra-passenger/issues) · [Discussions](https://github.com/drosemann/infra-passenger/discussions)*
