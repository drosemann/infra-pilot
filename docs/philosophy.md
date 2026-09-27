# The Middle Man principle

infra-passenger is deliberately the middle man: close enough to the
infrastructure to understand each change, but equipped with enough tooling to
make that work repeatable. It is anti-autopilot, not anti-automation. The tool
makes the state visible and the operator keeps the deciding click.

## Architecture by Mitte

These deliberately local comparisons are a decision framework, not a product
endorsement:

- **GLB, not GLA/GLE.** Choose the useful middle: enough capacity and a clear
  interface, without luxury abstraction for its own sake.
- **Fitness First, not McFit or Kieser.** A dependable, practical routine beats
  both bare-minimum shortcuts and premium ceremony. Operations should be
  usable every day.
- **Deutschlandticket, not Hessenticket/1. Klasse.** Prefer a broadly useful,
  predictable platform to a narrow special case or an over-specified tier.
- **nano, not pico/lite.** Use a small tool that remains understandable when a
  human has to edit the file at 02:00.
- **4.50€ Kantine, not 3€/6.50€.** The right trade-off is solid value: not
  suspiciously cheap, not needless status spending.

The resulting architecture is explicit Docker, documented APIs, readable
configuration, and commands that show their work. Automation is welcome when
it preserves the operator's ability to inspect, approve, and intervene.
