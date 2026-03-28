# Manual Capture Checklist

## Before Start

- Pick one AP subject only.
- Pick one exam packet only.
- Create one capture session id, for example: `2026-03-26_ap_calculus_ab_packet_01`.
- Create a folder with that id under `database/01_raw/sessions/`.

## Save During Capture

- Save the exam landing page HTML.
- Save the test page HTML after the first question loads.
- Save every useful API response as raw JSON.
- Save at least:
  - one screenshot of the packet overview
  - one screenshot of an MCQ item
  - one screenshot of an FRQ item
  - one screenshot of answer/explanation if available

## Minimum Data To Extract

- exam id
- subject
- exam title
- MCQ question list
- FRQ question list
- each question stem
- options for MCQ
- correct answer
- explanation
- assets referenced by the question
- knowledge point tags if shown

## Put Files Here

- raw HTML: `database/01_raw/html/`
- raw JSON: `database/01_raw/json/`
- copied request/response notes: `database/01_raw/network/`
- screenshots: `database/01_raw/screenshots/`
- session notes: `database/07_logs/`

## After Capture

- build one `exam_packet` file in `database/02_staging/exam_packets/`
- build one question file per question in `database/02_staging/questions/`
- move trusted final question files into `database/03_curated/ap/subjects/<subject>/mcq|frq/`
