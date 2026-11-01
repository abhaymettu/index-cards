# observability stack comparison

Quick reference so I stop re-deriving this every time someone asks "what should we use for monitoring."

## the options I keep coming back to

- **Prometheus + Grafana + Loki + Tempo** (self-hosted LGTM-ish): cheapest in licensing, most expensive in my time. Great if I already have k8s and someone who likes running stateful things.
- **Datadog**: everything works out of the box, UI is nice, bill is scary. Custom metrics and log ingestion are where it explodes.
- **Honeycomb**: best for debugging high-cardinality stuff. Weaker for classic infra dashboards. Pairs well with something else for host metrics.
- **Grafana Cloud**: same tools as self-hosted, someone else runs them. Free tier is decent for side stuff. Pricing by active series is easy to blow past.
- **OpenTelemetry collector in front of whatever**: not a backend, but the thing that keeps me from getting locked in.

## cost gotchas

- Cardinality is the real bill driver. One label with user ids and I'm toast.
- Logs cost more than metrics and traces combined most of the time. Sample or drop debug logs at the collector.
- Datadog host-based pricing gets weird with lots of small containers.
- Retention: 15 days hot is plenty, ship the rest to object storage if needed at all.
- Egress between regions/clouds quietly adds up when shipping telemetry.

## setup notes

- Instrument with OTel SDKs from day one, export OTLP, decide backend later.
- Run the collector as a sidecar or daemonset, not in-app exporters directly. Easier to change batching, retries, sampling.
- Tail-based sampling needs the collector to see whole traces, so it needs a gateway tier, not just agents.
- Alert on symptoms (error rate, latency p95/p99, saturation), not every CPU blip.
- Keep dashboards in code (Grafana JSON via provisioning or Terraform). Click-built dashboards rot.

## when to pick what

- Solo or tiny team, no ops appetite: Grafana Cloud free/pro, OTel everywhere.
- Mid team, budget exists, want speed: Datadog, but set usage alerts on day one.
- Debugging-heavy product with weird distributed bugs: Honeycomb plus cheap metrics from Prometheus.
- Compliance or data residency pressure: self-hosted, accept the toil.

## todo

- [ ] price out a real month of our log volume on each, not vendor calculators
- [ ] test tail sampling config locally with the collector
- [ ] check if exemplars link metrics to traces in the setup I'd pick
