---
id: RUNBOOK-062
type: runbook
title: Customer Portal WebSocket Disconnection Runbook
status: deprecated
owner: On-Call Engineer
created: '2025-09-02T09:47:36.203Z'
updated: '2025-08-13T02:07:36.364Z'
tags:
  - runbook
  - customer-portal
summary: Customer Portal WebSocket Disconnection Runbook
example: true
---

## Service

- **System**: [[SYSTEM-041|Customer Portal]]
- **Owner team**: Customer Portal Engineering
- **On-call rotation**: PagerDuty schedule "portal-oncall"
- **Slack channel**: #customer-portal-incidents
- **Runtime**: Node.js 20 / Socket.IO / AWS Application Load Balancer / Redis Pub/Sub

## Alerts

- `portal_websocket_disconnect_rate_high` - WebSocket disconnect rate exceeds 10% of active connections per minute
- `portal_websocket_reconnect_loop` - More than 5% of clients reconnecting more than 3 times in 5 minutes
- `portal_realtime_message_delivery_failure` - Real-time notification delivery failure rate exceeds 5%
- `portal_ws_server_memory_high` - WebSocket server process memory exceeds 80% of limit

## Diagnosis Steps

1. **Check ALB sticky session configuration** - WebSocket connections require sticky sessions on the load balancer; if the ALB is not forwarding reconnection attempts to the same server, clients will disconnect repeatedly after each reconnect.
2. **Check WebSocket server logs** - Filter portal WebSocket server logs for connection error events; look for `ECONNRESET`, heartbeat timeout, or `Authentication failed` messages to categorize disconnect causes.
3. **Check Redis Pub/Sub health** - The portal uses Redis for cross-server real-time message fanout; verify Redis is responding and that the WebSocket servers are successfully subscribed to their channels.
4. **Check for a recent deployment** - A rolling deployment without WebSocket drain causes active connections to drop; check #customer-portal-deployments to see if a deploy is in progress or recently completed.
5. **Check WebSocket server resource usage** - Run `kubectl top pods -n customer-portal -l component=websocket`; high memory usage can cause the Node.js event loop to lag, causing heartbeat timeouts and disconnects.

## Remediation Steps

1. **If caused by a rolling deployment**: Ensure future deployments use connection draining (preStop hook with 30-second grace period); for the current incident, the clients will reconnect automatically after the rolling deploy completes.
2. **If ALB sticky sessions are misconfigured**: Update the ALB target group to enable sticky sessions with a 1-hour duration; apply the change via Terraform and redeploy the load balancer configuration.
3. **If Redis Pub/Sub is unavailable**: Restart the Redis service and wait for WebSocket servers to re-subscribe; clients will miss messages during the outage window.
4. **If WebSocket servers are memory-exhausted**: Restart the WebSocket deployment pods: `kubectl rollout restart deployment/customer-portal-ws -n customer-portal`; investigate memory leak in the next sprint.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Post initial assessment in #customer-portal-incidents |
| 20 min | If not resolved: page Portal Tech Lead |
| 30 min | Engineering Manager paged if real-time features are fully down |
| 60 min | Consider disabling WebSocket features via feature flag and falling back to polling |

## Dashboards

- [Portal WebSocket Overview](https://grafana.example.com/d/portal-ws) - Connection count, disconnect rate, message delivery
- [Portal Redis Pub/Sub](https://grafana.example.com/d/portal-redis-pubsub) - Channel subscription health, message throughput
- [ALB Access Logs](https://cloudwatch.example.com/portal-alb) - WebSocket upgrade requests, sticky session distribution
- [Portal WebSocket Pods](https://grafana.example.com/d/portal-ws-pods) - Memory, CPU, connection count per pod
