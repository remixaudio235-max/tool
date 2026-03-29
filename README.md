# VN Live Arranger Studio (Professional Foundation)

Windows-first desktop application foundation for converting an existing beat/song into an editable semi-automatic live arranger workflow (Vietnamese organ/live performance oriented).

## Implemented in this milestone

- Production-friendly Python package scaffold (`app/`) with modular layers.
- Serializable domain models for project, sections, chords, stems, arrangement blocks, references, phrases, AI suggestions.
- Project save/load primitives.
- Professional UI shell (PySide6 + pyqtgraph):
  - toolbar actions
  - drag & drop source import
  - waveform view
  - project sidebar
  - section/chord editor tables
  - arranger block list
  - reference library list
- Source import with metadata extraction (sample rate, duration) and waveform rendering.
- Core deterministic analysis pipeline:
  - tempo
  - beats
  - bar grid
  - section proposal
  - key estimate
  - chord proposal (editable foundation)
- Rule-based arrangement foundation:
  - style resolver (Bolero VN, Ballad VN, Pop Ballad, Rumba VN)
  - Intro/Main/Outro block generation by rules
- Reference library service foundation with tag filtering.
- AI helper abstraction with mock suggestion provider.
- Initial tests for serialization, analysis, rule engine, reference filtering.

## Architecture (current)

- `main.py`: startup + logging
- `app/models`: serializable data models
- `app/services`: orchestration and app services
- `app/analysis`: deterministic analyzers
- `app/arranger`: rule engine and style mapping
- `app/ui`: shell UI components
- `app/utils`: logging/io/audio/validation helpers
- `presets`: style preset JSON stubs
- `tests`: pytest smoke and unit tests

## Run

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python main.py
```

## Test

```bash
pytest -q
```

## Roadmap / TODO (next milestones)

1. Editable bar grid interaction (drag/insert/delete markers) in waveform timeline.
2. Section split/merge/rename and role reassignment UI logic.
3. Chord editor write-back + confidence highlighting + keyboard workflow.
4. Demucs wrapper integration with cache manager and fallback UX.
5. Playback mixer with A/B source vs arrangement and block preview.
6. Export engine (full mix, arrangement-only, stems, block exports, project package).
7. Learning-memory case store integration in save/export workflows.
8. AI provider plugin registry (local/cloud adapters).

## Product philosophy

Automatic analysis proposes.
Rule engine builds.
User corrects the musical truth.
AI helps optionally.
User stays in control.
