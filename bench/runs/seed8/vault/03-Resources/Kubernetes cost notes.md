# Kubernetes cost notes

## Where the money actually goes
- Compute is ~70% of the bill, almost always. Nodes first, everything else later.
- Idle capacity is the big one. Check requested vs actually used CPU/mem per namespace before touching anything else.
- Cross-AZ traffic sneaks up. Chatty services spread across zones = surprise data transfer line item.
- Load balancers: one per Service type=LoadBalancer adds up fast. Consolidate behind an ingress.
- Orphaned PVCs and unattached disks. Check monthly, they never clean themselves.

## Requests and limits
- Requests drive scheduling AND cost. Limits mostly don't affect the bill.
- Most workloads I look at have requests 3-5x actual p95 usage. Start there.
- Set requests from p95 over at least 2 weeks, not a quiet weekend.
- Memory: keep limit = request, OOM kills are worse than slight overprovision.
- CPU limits: often skip them, throttling hurts latency more than it saves.
- VPA in recommend-only mode is a decent way to get numbers without it restarting stuff.

## Node strategy
- Spot/preemptible for stateless, retry-safe stuff. Needs PDBs and graceful shutdown that actually works (test it).
- Keep a small on-demand base pool for system pods and anything stateful.
- Mix instance types in spot pools so one capacity crunch doesn't kill everything.
- Bin-packing: fewer bigger nodes usually beats many small ones, but blast radius goes up. ~4-16 vCPU feels like the sweet spot.
- Autoscaler scale-down is slow by default. Tune the unneeded time and watch for pods blocking drain (local storage, no PDB, annotations).
- ARM nodes: ~20% cheaper for same perf in my tests, but check image builds are multi-arch first.

## Non-prod
- Scale dev/staging to zero overnight and weekends. Easy 60% savings on those clusters.
- Don't give staging prod-sized replicas "to be realistic". 1-2 replicas is fine.
- TTL on preview environments, otherwise they pile up forever.

## Visibility
- Label everything: team, env, service. Cost allocation is useless without it.
- Run a cost tool (opencost or similar) and look at it weekly, not quarterly.
- Alert on sudden spend jumps, not just monthly budget totals.

## TODO
- [ ] audit PVCs older than 90 days
- [ ] try VPA recommendations on the top 10 namespaces by spend
- [ ] check log volume, ingestion cost might be bigger than the nodes for some services
