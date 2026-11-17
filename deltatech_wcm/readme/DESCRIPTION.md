One dashboard for the ten technical pillars of World Class Manufacturing (WCM):
Safety, Cost Deployment, Focused Improvement, Autonomous Maintenance, Planned
Maintenance, Quality Control, Logistics and Customer Service, Early Equipment
Management, People Development, Environment and Energy.

Each pillar groups its indicators. Each indicator has a target, a warning
threshold and a traffic light: green, yellow, red, or "no data". The pillar
shows the worst state of its indicators.

Indicators read from Odoo:

- OEE availability, from the work centers (`mrp`);
- MTBF and MTTR, from the maintenance equipment (`maintenance`);
- quality control failure rate (`quality`) and scrap rate (`stock`, `mrp`);
- on-time deliveries, from the outgoing transfers (`stock`).

The other indicators, including the Safety and Focused Improvement (Kaizen)
placeholders, are entered manually until a dedicated module provides them.

The seed targets are placeholders: confirm them with the plant before use.
