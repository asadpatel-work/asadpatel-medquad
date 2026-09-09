# ADR-005: Multi-Turn Session Memory & Client-Side Cache Synchronization

## Status
**Accepted** (Implemented)

## Context
Clinical research workflows involve iterative, multi-turn consultations where clinicians progressively refine questions (e.g. asking about diagnostic markers, then staging criteria, then clinical trial protocols).
Key requirements:
1. Preserve conversational context and citations across multiple turns.
2. Provide a Consultation History Sidebar enabling switching between distinct research investigations.
3. Maintain state resilience during serverless container scale-downs, cold starts, and multi-tab browser usage.

## Decision
We implemented a **Hybrid Backend-Frontend Session Synchronization Architecture**:
1. **Backend State Management (`backend/services/memory_service.py`):**
   - Singleton `MemoryService` maintaining `SessionState` structures keyed by `session_id`.
   - Stores chronological `ChatMessage` objects containing text, citations, reasoning steps, and metadata.
   - Provides REST endpoints: `GET /api/v1/sessions` (session list), `GET /api/v1/sessions/{session_id}` (full history), and `DELETE /api/v1/sessions/{session_id}`.
2. **Frontend Dual-Layer Cache (`backend/static/index.html` & `frontend/src/App.tsx`):**
   - Renders a left-hand collapsible **Consultation History Sidebar** with real-time keyword search and message counters.
   - Persists session lists and message history in browser `localStorage` as a resilient local backup.
   - Synchronizes seamlessly with backend session state on application load.

## Consequences
- **Positive:**
  - Fast, instantaneous consultation switching and history persistence.
  - Resilience against serverless cold starts and container instance recycling.
  - Clean separation between active session memory and historical archive.
- **Negative:**
  - In-memory backend state is instance-local unless backed by an external store (e.g., Cloud SQL / Firestore, which is architected for Phase 2).
