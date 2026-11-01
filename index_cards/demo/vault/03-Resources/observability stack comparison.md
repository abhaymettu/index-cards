# observability stack comparison

Quick reference for picking/defending a stack. Not exhaustive, just what I keep forgetting.

## options I've actually touched

- **Prometheus + Grafana + Loki + Tempo**: the OSS "LGTM" route. Cheap in licenses, expensive in my time.
- **Datadog**: everything works day one. Bill is the problem.
- **Honeycomb**: best for high-cardinality debugging. Weaker on classic infra metrics.
- **Elastic/ELK**: fine for logs, heavy to run, JVM tuning never ends.
- **OpenTelemetry collector in front of anything**: always worth it, see below.

## cost notes

- Datadog pricing bites on custom metrics + log indexing. Tags with unbounded values = surprise invoice.
- Self-hosted isn't free: budget ~0.25 FTE for upkeep once past a handful of services.
- Loki cheap for storage since it only indexes labels, but grep-style queries over big ranges are slow.
- Honeycomb priced on events, so sampling matters. Head sampling loses the interesting errors; tail sampling in the collector fixes that.

## practical gotchas

- Cardinality kills Prometheus first. Watch `prometheus_tsdb_head_series`. Never put user id / request id in labels.
- Retention: 15d local on Prometheus is fine, anything longer → Thanos or Mimir, not bigger disks.
- Trace-to-log correlation only works if trace id is in the structured log line. Do this in the logging middleware once, not per-service.
- Alert on symptoms (error rate, latency p99, saturation), not causes. Cut pager noise by half doing just this.
- Dashboards rot. Keep one per service from a template, delete the rest quarterly.

## otel collector setup

- Apps send OTLP to local collector, collector fans out to backend(s).
- Makes switching vendors a config change, not a re-instrumentation.
- Put batch + memory_limiter processors in, in that order (memory_limiter first).
- Run as daemonset/sidecar for agents, plus a small gateway tier for tail sampling.

## decision rules

- Small team, <10 services, budget exists → Datadog or Honeycomb, don't self-host.
- Cost-sensitive, someone owns infra → LGTM + otel.
- Debugging weird distributed latency → want traces with real querying, Honeycomb-style.
- Whatever I pick: instrument with OTel, structured JSON logs, RED metrics per service.

## todo

- [ ] price out log volume per day before comparing quotes
- [ ] test Tempo search on real trace volume
- [ ] write the logging middleware snippet into the notes vault
