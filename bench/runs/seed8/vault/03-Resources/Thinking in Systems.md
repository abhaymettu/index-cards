# book notes on Thinking in Systems

## core vocabulary I keep forgetting
- **Stock**: the thing that accumulates (water in tub, backlog, tech debt, cash). Only changes via flows.
- **Flow**: inflow/outflow rate. Change the flow, the stock moves slowly. Stocks give systems inertia.
- **Feedback loop**: stock level influences its own flow.
  - *Balancing*: goal-seeking, stabilizes (thermostat, autoscaler, on-call fatigue pushing people to fix alerts).
  - *Reinforcing*: runaway growth or collapse (compounding interest, bad code attracting more bad code).
- **Delay**: gap between action and visible result. Most overshoot/oscillation comes from delays + impatient correction.

## how I apply it at work
- Before "fixing" a metric, draw the stocks and flows on paper. Takes 10 min, usually kills the first idea.
- Backlog is a stock. Arguing about how fast we close tickets ignores the inflow. Cut inflow (better intake, saying no) before adding throughput.
- Retry storms = reinforcing loop hiding inside a balancing one. Need backoff + jitter + circuit breaker to cap it.
- Autoscaling with slow warmup = delay in the loop, so it overshoots then thrashes. Lengthen the cooldown or scale on a leading signal.
- When a team keeps "fixing" the same incident, ask what loop is regenerating it.

## leverage points (rough order, weak to strong)
1. Numbers/parameters (timeouts, thresholds). Easy to tweak, rarely matters much.
2. Buffer sizes. Big buffers = stability but slow and costly.
3. Information flows. Making data visible to the people who can act on it is surprisingly powerful. Cheap too.
4. Rules of the system (incentives, constraints).
5. Goals of the system. Everything else bends toward the goal.
6. Mindset/paradigm that produced the goals.

My takeaway: I spend most effort at level 1 and should push toward 3 and 4.

## common traps (archetypes)
- **Policy resistance**: everyone pulls toward a different goal, so nothing moves. Align goals first.
- **Tragedy of the commons**: shared resource, no feedback to the user (shared CI runners, shared staging env). Fix by making usage visible or priced.
- **Drift to low performance**: standards slip because the baseline is the recent past. Anchor to an absolute standard.
- **Shifting the burden**: quick patch relieves symptoms and weakens the real fix. Watch for "temporary" workarounds.
- **Success to the successful**: winners get more resources, losers starve. Check who gets the good projects.

## habits to keep
- Ask "what's the stock?" and "where's the delay?" in design reviews.
- Expect surprises, run small experiments, and watch for side effects.
- Don't optimize one part at the expense of the whole. Check the boundary of what I'm modeling.
- Re-read the leverage points chapter once a year.
