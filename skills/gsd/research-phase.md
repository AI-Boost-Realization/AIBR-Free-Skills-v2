---
name: gsd:research-phase
description: Research how to implement a phase before planning
argument-hint: "[phase]"
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - Write
  - WebFetch
  - WebSearch
---

<objective>
Comprehensive research on HOW to implement a phase before planning.

This is for niche/complex domains where training data is sparse or outdated. Research discovers:
- What libraries exist for this problem
- What architecture patterns experts use
- What the standard stack looks like
- What problems people commonly hit
- What NOT to hand-roll (use existing solutions)

Output: RESEARCH.md with ecosystem knowledge that informs quality planning.
</objective>

<context>
Phase number: $ARGUMENTS (required)

**Load project state:**
@.planning/STATE.md

**Load roadmap:**
@.planning/ROADMAP.md

**Load phase context if exists:**
Check for `.planning/phases/XX-name/{phase}-CONTEXT.md` - bonus context from discuss-phase.
</context>

<process>
1. Validate phase number argument (error if missing or invalid)
2. Check if phase exists in roadmap - extract phase description
3. Check if RESEARCH.md already exists (offer to update or use existing)
4. Load CONTEXT.md if it exists (bonus context for research direction)
5. Analyze phase to identify knowledge gaps
6. Determine research domains (architecture, ecosystem, patterns, pitfalls)
7. Execute comprehensive research via official docs, web search, library documentation
8. Cross-verify all findings
9. Create RESEARCH.md with actionable ecosystem knowledge
10. Offer next steps (plan the phase)
</process>

<when_to_use>
**Use research-phase for:**
- 3D graphics (Three.js, WebGL, procedural generation)
- Game development (physics, collision, AI, procedural content)
- Audio/music (Web Audio API, DSP, synthesis)
- Shaders (GLSL, Metal, ISF)
- ML/AI integration (model serving, inference, pipelines)
- Real-time systems (WebSockets, WebRTC, sync)
- Specialized frameworks with active ecosystems
- Any domain where "how do experts do this" matters

**Skip research-phase for:**
- Standard web dev (auth, CRUD, REST APIs)
- Well-known patterns (forms, validation, testing)
- Simple integrations with clear docs
- Commodity features
</when_to_use>

<success_criteria>
- [ ] Phase validated against roadmap
- [ ] Domain/ecosystem identified from phase description
- [ ] Comprehensive research executed (official docs + web search)
- [ ] All findings cross-verified with authoritative sources
- [ ] RESEARCH.md created with ecosystem knowledge
- [ ] Standard stack/libraries identified
- [ ] Architecture patterns documented
- [ ] Common pitfalls catalogued
- [ ] What NOT to hand-roll is clear
- [ ] User knows next steps (plan phase)
</success_criteria>
