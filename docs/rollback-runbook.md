# Rollback Runbook

## Trigger

Roll back when one or more of the following is observed after a release:

- readiness failures
- sustained 5xx error rate above the release threshold
- unacceptable latency regression
- crash loops or repeated restarts
- a confirmed security regression

## Immediate actions

1. Stop further production promotions.
2. Record the release tag, commit SHA, start time, and alert.
3. Inspect Helm history:

   ```bash
   helm -n commerce-prod history commerce-platform
   ```

4. Restore the previous healthy revision:

   ```bash
   helm -n commerce-prod rollback commerce-platform PREVIOUS_REVISION --wait --timeout 5m
   ```

5. Verify:

   ```bash
   kubectl -n commerce-prod get pods
   kubectl -n commerce-prod rollout status deployment --timeout=5m
   ```

6. Confirm AOM error, latency, saturation, and availability recovery.

## Completion criteria

- minimum ready replicas restored
- 5xx rate below threshold
- p95 latency returned to baseline
- smoke test passed
- incident owner recorded

## Follow-up

Open a post-incident issue with the timeline, impact, root cause, detection gap,
corrective actions, and a test that prevents recurrence.

