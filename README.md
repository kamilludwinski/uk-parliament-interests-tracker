# uk-parliament-interests-tracker

A data pipeline and analytics project for collecting, normalizing, and exploring publicly available UK Parliament Members’ financial interests and related disclosures.

This project is intended as a transparency, research, and data engineering tool built on top of official UK Parliament data.

## Overview

`uk-parliament-interests-tracker` ingests publicly available parliamentary interests data, stores raw source material, normalizes it into structured records, and makes it easier to analyze categories such as:

- Employment and earnings
- Donations and support
- Gifts, benefits, and hospitality
- Visits outside the UK
- Shareholdings
- Other registrable interests

The long-term goal is to provide a clean dataset that can power:

- dashboards
- change feeds
- alerts
- sector/company analysis
- conflict-of-interest research
- visualisations

## Data source

This project uses publicly available UK Parliament information, including data from the Register of Members’ Financial Interests and related parliamentary sources.

Primary source:

- https://members.parliament.uk/
- https://www.parliament.uk/business/publications/commons/register-of-members-interests/

## Licence

Contains Parliamentary information licensed under the Open Parliament Licence v3.0.

- Open Parliament Licence: https://www.parliament.uk/site-information/copyright-parliament/open-parliament-licence/

This project may retrieve, store, transform, and display Parliamentary information in accordance with the Open Parliament Licence v3.0.

## Attribution

As required by the Open Parliament Licence v3.0:

> Contains Parliamentary information licensed under the Open Parliament Licence v3.0.

## Disclaimer / Non-endorsement

This project is **not affiliated with, endorsed by, or officially connected to the UK Parliament**, the House of Commons, the House of Lords, or any related parliamentary body.

This is an independent project for research, transparency, and software engineering purposes only.

The project does **not** claim official status, and the use of Parliamentary information does **not** imply endorsement by Parliament.

## Project goals

- Build a reliable ingestion pipeline for UK Parliament interests data
- Preserve raw source documents for replay/debugging
- Normalize semi-structured disclosures into queryable tables
- Track changes over time
- Enrich organizations/companies with additional metadata
- Power future dashboards and analytics tools

## Planned architecture

The project is designed around three data layers:

1. **Raw layer**
   - Store original source payloads / pages
   - Immutable, replayable ingestion

2. **Normalized layer**
   - Parse disclosures into structured records
   - Stable schema for downstream use

3. **Derived layer**
   - Sector tagging
   - Organization/entity resolution
   - Change detection
   - Aggregations and analytics

## Status

🚧 Early development / work in progress

Initial focus:

- data ingestion
- raw storage
- parsing selected categories
- building a stable schema before any public dashboard

## Notes

- This repository is focused on public-interest data engineering and analytics.
- Source data may change over time and is provided by Parliament "as is".
- No warranty is made as to completeness, correctness, or continued availability of upstream data.

## Future ideas

- MP profile explorer
- Recent changes feed
- Sector/company relationship mapping
- Shareholding transparency views
- Alerts for newly declared interests
- Conflict-of-interest analysis

## Contributing

Contributions, ideas, and issue reports are welcome once the core schema stabilizes.

## Legal note

This repository is intended to comply with the Open Parliament Licence v3.0.

If you believe any data or presentation in this project should be amended or removed, please open an issue or contact the repository owner.
