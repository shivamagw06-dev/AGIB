# AGI Mission Control V1

**Architecture status:** v1.0.1 LOCKED  
**Role:** Administrator-only operations cockpit.  
**Not:** intelligence engine · recommendation engine · client page · mutator

## Rules

- Read-only aggregation of IOC, CMS, CID, Academy, CA, IO, DVC, ECP, …
- Never modifies research, House Views, or recommendations
- Never visible to public/clients

## Admin

`/admin/mission-control` — auto-refresh 30s, dark institutional theme

## Flags

`MISSION_CONTROL`, `MISSION_CONTROL_APIS`, `MISSION_CONTROL_PLATFORMS`, `MISSION_CONTROL_COVERAGE`, `MISSION_CONTROL_KNOWLEDGE`, `MISSION_CONTROL_ALERTS`, `MISSION_CONTROL_EVENTS`, `MISSION_CONTROL_REPORTS`

## APIs

- `GET /v1/mission-control/health`
- `GET /v1/mission-control/dashboard`
- `GET /v1/mission-control/quality-gates`
- `GET /v1/mission-control/report`
- `POST /v1/mission-control/acknowledge`
