# UltiClock System Test Plan

## Core Alarm Scenarios
- [ ] Fresh Boot Missed Alarm Recovery
- [ ] Calendar Event → Alarm Creation Latency (<2s)
- [ ] Concurrent Snooze Requests Handling
- [ ] GPS Time Fallback → NTP Sync Recovery

## Calendar Synchronization
- [ ] Event Creation → Alarm Scheduled (Within 15m Sync Window)
- [ ] Event Time Modification → Alarm Rescheduled
- [ ] Event Deletion → Alarm Canceled (Only if not snoozed)
- [ ] Full Calendar Outage → Database Fallback Operation
- [ ] Multi-Calendar Conflict Resolution

## Snooze-Specific Cases
- [ ] SNOOZE-1: Basic Snooze Persistence Through Sync
- [ ] SNOOZE-2: Snooze Then Original Event Deletion
- [ ] SNOOZE-3: Multiple Sequential Snoozes
- [ ] SNOOZE-4: Snooze During Calendar Sync
- [ ] SNOOZE-5: Max Snooze Duration Boundary (24h)

## Critical Failure Modes
- [ ] POWER-1: Power Loss During Alarm Trigger
- [ ] TIME-1: Incorrect System Time Detection/Correction
- [ ] DB-1: Database Corruption → Emergency Recovery
- [ ] NET-1: Internet Loss During Sync → Graceful Degradation

## Plugin Integration
- [ ] PLUGIN-1: Multiple Plugin Execution Order
- [ ] PLUGIN-2: Plugin Failure → Core Alarm Still Triggers
- [ ] PLUGIN-3: Snooze-Specific Plugin Configuration

## Snooze Integrity Guardrails
- [ ] GUARD-1: Calendar Sync Preserves Snoozed Alarms
- [ ] GUARD-2: Snoozed Alarms Immune to Calendar Changes
- [ ] GUARD-3: Manual Snooze Overrides Calendar Events
- [ ] GUARD-4: Snooze History Logging (Last 3 Snoozes)
- [ ] GUARD-5: Snoozed Alarm Blocks New Calendar Instance
- [ ] GUARD-6: Original Event Marked Triggered When Snoozed
- [ ] GUARD-7: Multiple Snoozes Maintain Original Event Link
- [ ] GUARD-8: Calendar Event Recreation After Snooze Expiry 