# book notes on Thinking in Systems

## core vocab I keep forgetting

- **stock** = thing you can count at a single instant (water in tub, tech debt items, open tickets). **flow** = rate that changes it. Stocks are the memory of the system.
- **balancing loop** = pushes toward a goal, stabilizes (thermostat, autoscaler, on-call fatigue pushing people to rotate out).
- **reinforcing loop** = amplifies, either growth or collapse (more users -> more data -> better product -> more users. Also: more bugs -> less time -> more shortcuts -> more bugs).
- **delay** = gap between action and visible effect. Most overshoot/oscillation comes from here.
- **buffer** = big stock that absorbs shocks. Bigger buffer = more stable but slower to change.

## how I'm actually using it at work

- Before proposing a fix, sketch the loop on paper. If I can't name the stock and the flows, I don't understand the problem yet.
- Ask "what's the delay?" for any metric I'm watching. Hiring, refactors, and culture changes all lag by months, so don't judge them after two weeks.
- Autoscaling flapping = classic balancing loop with a delay. Fix is longer cooldown / smoothing the signal, not a lower threshold.
- Backlog growth: check inflow vs outflow before adding people. Often the cheaper lever is cutting inflow (say no, dedupe, kill dead requests).
- When a team "optimizes its own metric" and hurts someone else, that's local rationality + bounded view. Widen the boundary of the diagram.

## leverage points (rough order, weakest to strongest)

1. Constants and parameters (timeouts, quotas, limits). Everyone fiddles here, least payoff.
2. Buffer sizes.
3. Structure of stocks and flows.
4. Delays relative to rate of change.
5. Strength of balancing loops (are alarms and feedback actually wired up?).
6. Information flows, who sees what and when. Cheap and underrated.
7. Rules of the system (incentives, constraints).
8. Goals.
9. Paradigm / the mindset the system comes from.

Takeaway: adding visibility (dashboards people actually look at, a postmortem that gets read) beats tweaking numbers.

## traps (archetypes) to watch for

- **Fixes that fail / shifting the burden**: quick patch relieves the symptom, real fix never happens, dependence on the patch grows. Feature flags and manual runbooks are my usual culprits.
- **Drift to low performance**: standards slide because the baseline is the recent past. Anchor to an absolute target.
- **Escalation**: two teams each ratchet up in response to the other.
- **Tragedy of the commons**: shared cluster, shared CI. Needs feedback to the people consuming it (cost visibility, quotas).
- **Seeking the wrong goal**: system hits the metric but not the intent. Check what is being measured vs what I care about.

## reminders

- Resist pushing on the obvious lever. Counterintuitive results are normal.
- Draw the diagram, then ask what I left outside the boundary.
- Re-read the leverage points chapter before any planning cycle.
- Systems have a history; the current behavior is usually explained by past structure, not current people.
