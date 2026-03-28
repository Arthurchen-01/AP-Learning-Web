# Database Layout

This folder stores scraped exam data, normalized templates, and the study records derived from them.

## Folders

- `00_inbox`
  Temporary drop zone. Put ad hoc files here before sorting them.

- `01_raw`
  Original captures. Never edit these by hand.
  - `sessions`: one folder per scraping session
  - `html`: saved page HTML
  - `json`: raw API responses
  - `network`: request/response logs, HAR-like exports, copied payloads
  - `screenshots`: page screenshots used for manual verification

- `02_staging`
  Parsed but not yet finalized data.
  - `exam_packets`: exam-level packet metadata
  - `questions`: normalized question objects
  - `answers`: normalized answer keys and user-answer-related structures
  - `explanations`: parsed explanations
  - `knowledge_points`: extracted or inferred knowledge point tags

- `03_curated`
  Final study-ready data.
  - `ap/subjects/<subject>/mcq`: finalized AP multiple-choice questions by subject
  - `ap/subjects/<subject>/frq`: finalized AP free-response questions by subject
  - `ap/full_exam`: full AP exam bundles referencing MCQ and FRQ items
  - `ap/subject_index`: AP subject metadata and aliases
  - `sat/...`: optional compatibility area if SAT data is kept later

- `04_assets`
  Binary assets referenced by questions or notes.
  - `images`
  - `audio`
  - `attachments`

- `05_indexes`
  Lookup and relationship files.
  - `exam_index`
  - `question_index`
  - `knowledge_map`

- `06_exports`
  Derived outputs for other tools.
  - `anki`
  - `csv`
  - `jsonl`

- `07_logs`
  Scraping logs, parse logs, manual audit notes.

- `08_templates`
  Reusable templates for manual capture and future scripts.
  - `ap/exam_packet_template`
  - `ap/question_template`
  - `ap/knowledge_point_template`
  - `ap/manual_import_checklist`

## Basic Rule

1. Save untouched source material in `01_raw`.
2. Convert and clean in `02_staging`.
3. Only put trusted final data in `03_curated`.
4. Prefer converting every source into the same AP-oriented template shape so future real past papers can be imported consistently.
