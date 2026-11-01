# book notes on Thinking in Systems

Re-read this over a couple weekends. Keeping the stuff I actually use at work, not a full summary.

## Core vocabulary

- **Stock**: the thing that accumulates (queue depth, tech debt, cash, trust). Can only change via flows.
- **Flow**: inflow/outflow rates. Stocks change slowly, flows change fast. That mismatch explains a lot of "why isn't this fixed yet."
- **Balancing loop**: pushes toward a goal (autoscaler, thermostat, on-call fatigue pulling people out).
- **Reinforcing loop**: snowballs either way (more users -> more data -> better product; or flaky tests -> ignored failures -> more flakiness).
- **Delay**: the sneaky one. Feedback arrives late so you overshoot. See: hiring, scaling up, retries.

## Things I've applied

- When a metric keeps oscillating, look for a delay in the loop before blaming the controller. Autoscaler thrash was basically this: cooldown too short relative to warmup time.
- Retry storms = reinforcing loop hiding inside what looked like a balancing one. Add backoff + jitter, cap total retries, shed load at the edge.
- Before adding a fix, ask: which stock is this actually draining? If I can't name it, I'm probably treating a symptom.
- Draw the loop on paper first. Takes 10 min, usually kills half the bad ideas.

## Leverage points (rough order, weakest to strongest)

1. Tweaking numbers (timeouts, limits, thresholds). Cheap, rarely transformative.
2. Buffer sizes. Bigger buffers calm things but make the system slower to respond.
3. Information flows. Making data visible to the people who can act on it is underrated. Cheap and strong.
4. Rules of the system (incentives, constraints).
5. Goals. Whatever the system is optimizing, it will optimize.
6. Mindset/paradigm that produced the goals. Hardest to move.

My takeaway: I default to level 1 way too often. Try for 3 or 4 first.

## Traps to watch for

- **Policy resistance**: everyone pulling toward a different goal, so fixes get cancelled out.
- **Drift to low performance**: standards slip because the baseline keeps being reset to "recent history."
- **Shifting the burden**: quick patch erodes the ability to fix the real thing. Hotfix culture is this.
- **Success to the successful**: winners get more resources, losers starve. Watch for it in team staffing.
- **Seeking the wrong goal**: optimizing for a proxy (ticket count, coverage %) and getting the proxy, not the outcome.

## To revisit

- Reread the chapter on resilience vs. efficiency before the next capacity planning round.
- Try a causal loop diagram on the incident backlog problem.
- Check whether our alerting is an information flow fix or just noise.
