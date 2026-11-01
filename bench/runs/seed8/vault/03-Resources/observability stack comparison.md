# observability stack comparison

Quick reference for picking between the setups I've run or evaluated. Not exhaustive, just what bit me.

## Self-hosted OSS (Prometheus + Grafana + Loki + Tempo)

- Cheapest per GB at scale, but ops cost is real. Budget someone's time for upgrades and storage tuning.
- Prometheus: great for metrics, falls over on high cardinality. Watch label explosions (user IDs, request paths with IDs baked in).
- Long-term retention needs Thanos or Mimir. Single Prometheus alone = ~2 weeks comfortable.
- Loki is cheap because it only indexes labels. Full-text grep over huge ranges is slow.
- Tempo is fine for traces if you already have trace IDs in logs. Without that correlation it's half useful.
- Alertmanager routing config is powerful but easy to get wrong. Test with `amtool` before deploying.

## Managed SaaS (all-in-one vendors)

- Fastest time to value. Agents + auto-instrumentation gets dashboards in an afternoon.
- Pricing is the trap: per-host, per-custom-metric, per-indexed-log-GB, per-trace span. Bills surprise you around month 3.
- Set hard caps on custom metrics and log ingest early. Add exclusion filters for health checks and debug logs.
- Lock-in is mostly in dashboards/alerts/query language, not data. Instrument with OpenTelemetry so the collector can be repointed.
- Support quality varies a lot; worth asking for a trial with real prod traffic.

## OpenTelemetry layer

- Use the OTel Collector as the one egress point. Lets me fan out to two backends during a migration.
- SDK auto-instrumentation is good for HTTP/DB clients, patchy for queues and custom protocols.
- Sampling: head sampling is simple but drops rare errors. Tail sampling in the collector keeps errors/slow traces but needs memory and sticky routing.
- Semantic conventions still shift between versions. Pin versions and read changelogs before bumping.

## Decision shortcuts

- Small team, <20 services, little ops time → managed SaaS with strict caps.
- Cost-sensitive, steady high volume, someone who likes infra → self-hosted OSS.
- Unsure → OTel everywhere, start managed, keep the exit door open.

## Gotchas to remember

- Logs, metrics, traces are only useful together. Make sure trace ID shows up in every log line.
- Alert on symptoms (latency, error rate, saturation), not every cause.
- Dashboards rot. Review quarterly, delete unused ones.
- Retention policy decided up front saves a painful conversation later.
