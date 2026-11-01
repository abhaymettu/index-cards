# Kubernetes cost notes

## Where the money actually goes
- Compute is ~70-80% of the bill. Everything else (LB, egress, storage) is noise until compute is sorted.
- Idle headroom is the big one. Nodes at 30% real utilization while requests say 80%. Requests are the lie, usage is the truth.
- Cross-AZ traffic sneaks up. Chatty services spread over zones = surprise egress line item.
- Orphaned stuff: unattached PVs, old load balancers from deleted namespaces, snapshots nobody remembers.

## Requests and limits
- Set requests from p95 usage over ~2 weeks, not from gut feel or copy-paste from another service.
- CPU limits mostly cause throttling, not savings. I usually set memory limit = request and leave CPU limit off (or very loose).
- VPA in recommend-only mode is a good way to get numbers without letting it restart pods.
- Check for pods with requests 10x what they use. Quick win, happens constantly.

## Node strategy
- Spot/preemptible for stateless + anything that tolerates a restart. Keep a small on-demand baseline.
- Diversify instance types in spot pools, otherwise one capacity crunch kills the whole pool.
- Bin-packing: fewer big nodes waste less on daemonset overhead, but blast radius goes up. Mid-size is the compromise.
- Autoscaler scale-down delay is worth tuning. Defaults keep nodes around longer than needed.
- ARM nodes = ~20% cheaper for the same work, if images are multi-arch. Check base images first.

## Dev / non-prod
- Scale non-prod to zero nights and weekends. Cron-based scale down is crude but works.
- Shared dev cluster with namespace quotas beats one cluster per team.
- TTL on preview environments, otherwise they live forever.

## Visibility
- Label everything with team/owner/env. Cost allocation is useless without it.
- Run a cost tool that breaks down by namespace and label. Look at it weekly, not quarterly.
- Alert on sudden daily spend jump, not just monthly budget.

## Todo
- [ ] audit requests vs usage for top 20 deployments
- [ ] check which images lack arm64 builds
- [ ] find unattached volumes
- [ ] set TTL policy for preview namespaces
- [ ] review log retention, logging cost might be sneaky too
