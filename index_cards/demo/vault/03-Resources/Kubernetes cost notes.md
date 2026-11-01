# Kubernetes cost notes

## Where the money actually goes
- Compute is ~70-80% of the bill. Nodes, not pods. Pods only matter via what they *request*.
- Egress and cross-AZ traffic is the sneaky second. Chatty services spread across zones add up quietly.
- Load balancers: one per Service type=LoadBalancer is wasteful. Consolidate behind an ingress controller.
- Orphaned PVCs and old snapshots. Check every few months, they never clean themselves.

## Requests vs limits
- Scheduler bills me for requests, not usage. Over-requested = paying for idle.
- Rule of thumb: set requests near p90 of real usage, memory limit ~ request (or a bit above), CPU limit often skip to avoid throttling.
- Look at actual usage over 2+ weeks before touching anything, not a single day.
- VPA in recommend-only mode is good enough for a first pass. Don't let it auto-restart prod stuff.

## Node strategy
- Spot/preemptible for stateless, interruption-tolerant workloads. Keep a small on-demand baseline.
- Mix instance types in the pool so spot capacity doesn't dry up all at once.
- Bin-packing: fewer, larger nodes usually waste less than many tiny ones, but blast radius goes up. Middle size wins.
- Cluster autoscaler / Karpenter scale-down is only as good as PDBs and pod annotations allow. Check what's blocking drains (`safe-to-evict`, local storage, strict PDBs).

## Dev and staging
- Scale non-prod to zero nights and weekends. Biggest easy win, probably 50%+ of non-prod spend.
- Shorter TTLs on preview environments. Forgotten ones pile up.
- Don't mirror prod replica counts in staging. 1 replica is fine for most things.

## Visibility
- Label everything by team/service/env or the cost report is useless.
- Run a cost tool (OpenCost or similar) and look at the "idle" and "efficiency" numbers first.
- Set a monthly review. 30 min, top 5 namespaces by cost, ask why each is that size.

## Gotchas
- Savings plans / reserved commitments: commit only to the baseline after right-sizing, not before.
- HPA with a low CPU target plus inflated requests = runaway replica count.
- Logging and metrics volume can cost more than the workloads producing them. Drop debug logs and high-cardinality labels.
- Image pulls from a different region/registry add egress and slow cold starts. Mirror locally.

## TODO
- [ ] audit PVCs without a bound pod
- [ ] turn on recommend-only VPA in one namespace
- [ ] schedule non-prod shutdown
