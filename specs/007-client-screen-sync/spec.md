# Feature Specification: Automatic Client Screen Refresh

**Feature Branch**: `007-client-screen-sync`  
**Created**: 2026-05-04  
**Status**: Draft  
**Input**: User description: "When game state changes on server, client screen updates automatically."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See Opponent's Changes Without Manual Action (Priority: P1)

A player is watching the battle screen after making their turn. Another player reduces dice for a combatant. The watching player's screen automatically reflects the updated dice count without requiring them to press any key or re-open a menu.

**Why this priority**: Core multiplayer value — without this, players cannot trust what they see on screen and must constantly poll for updates manually. This is the minimum viable version of real-time collaboration.

**Independent Test**: Open two clients connected to the same session. From client A, reduce a player's dice. Client B's displayed state should update to show the new dice count without client B's operator taking any action.

**Acceptance Scenarios**:

1. **Given** two clients are connected and viewing battle state, **When** client A reduces dice for a player, **Then** client B's screen displays the updated dice count within 2 seconds without client B pressing any key.
2. **Given** a client is idle at the main menu, **When** any connected client modifies game state, **Then** the idle client's displayed information refreshes to reflect the change.
3. **Given** a client is connected and another client adds a new player, **Then** the connected client's player list updates to include the new player automatically.

---

### User Story 2 - Live Lock Status Visibility (Priority: P2)

A player attempts to edit a combatant. Before submitting the edit, they can see that another player's lock indicator appeared on screen automatically — without needing to retry and receive a denial.

**Why this priority**: Prevents wasted interactions. Players spend less time getting blocked by surprises and can coordinate editing turns with awareness of current lock state.

**Independent Test**: With two clients open, client A acquires a lock. Client B's display should show the lock indicator for that player without client B initiating any action.

**Acceptance Scenarios**:

1. **Given** client A and client B are viewing battle state, **When** client A acquires a lock on a player, **Then** client B sees the lock indicator for that player automatically.
2. **Given** a player lock indicator is visible on client B, **When** client A releases the lock, **Then** the lock indicator disappears from client B's screen automatically.

---

### User Story 3 - Confirm Own Changes Reflected Immediately (Priority: P3)

A player submits a change (add player, reduce dice, switch cliché) and sees the result reflected on their own screen immediately after the action, without needing to navigate back to a display screen.

**Why this priority**: Provides confidence that commands were received and applied correctly. Reduces confusion and repeated submissions.

**Independent Test**: From a single client, add a player. The player list visible on screen should reflect the new player immediately after the command is submitted.

**Acceptance Scenarios**:

1. **Given** a client submits an "add player" command, **When** the server processes it, **Then** the player appears in the client's own battle display without requiring additional navigation.
2. **Given** a client reduces dice for a player, **When** confirmed by server, **Then** the updated dice count is visible on that client's screen immediately.

---

### Edge Cases

- What happens when the network connection drops while a state update is in transit? The display should remain at the last known state without showing corrupt or partial data.
- How does the display behave if multiple rapid changes arrive in quick succession? All changes must be reflected accurately; no updates should be silently dropped.
- What happens when a client is in the middle of typing input and a state update arrives? The state must be stored and displayed at the next natural opportunity without interrupting the user's current input.
- What if the server sends a state update while no players exist yet? The display should handle an empty player list gracefully.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The client MUST display updated game state automatically whenever the server broadcasts a state change, without requiring operator input.
- **FR-002**: The client MUST display lock acquisition and release events automatically as they occur, without requiring operator input.
- **FR-003**: State updates MUST be reflected in the client display within 2 seconds of the server broadcasting the change.
- **FR-004**: The client display MUST remain accurate under rapid successive state changes — no updates may be silently dropped or overwritten with stale data (as measured by SC-003).
- **FR-005**: State updates received while operator input is in progress MUST be queued and displayed at the next natural screen refresh, without discarding the update or interrupting the input flow.
- **FR-006**: The client's displayed state MUST NOT diverge from server state for more than 2 seconds under normal network conditions.
- **FR-007**: An automatic screen refresh MUST NOT cause data loss of partially entered user input. Visual redraw of the screen during a refresh is acceptable provided the input data remains intact in the terminal's input buffer and is submitted correctly when the operator presses Enter.

### Key Entities

- **Game State**: The authoritative snapshot of all players, their clichés, dice counts, and lost dice — owned by the server and broadcast to all clients on change.
- **Lock Indicator**: A visual marker on a player entry showing which connected user, if any, currently holds edit rights for that player.
- **Screen Refresh**: A client-side operation that redraws the visible battle state to match the latest received server snapshot.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: State changes made by one client are visible on all other connected clients within 2 seconds, with no manual action required from the receiving clients.
- **SC-002**: Lock acquisition and release events are visible on all connected clients within 2 seconds of the event occurring.
- **SC-003**: Zero state updates are silently dropped under normal network conditions when multiple changes occur within a 5-second window.
- **SC-004**: A player can participate in a full multiplayer session — observing all other players' changes in real time — without ever manually requesting a state refresh.

## Assumptions

- The server already broadcasts state change events to all connected clients; this feature concerns how the client *displays* those events, not whether they are transmitted.
- A client's operator may be idle at a menu or prompt between turns; the auto-refresh must work in both active and idle states.
- Network connectivity is stable; reconnection behavior and offline resilience are out of scope for this feature.
- The display refresh only affects the information view — it does not auto-submit any pending user input or navigate menus on the user's behalf.
- Multi-battle support remains out of scope per the project PRD; this feature applies to the single shared battle session.
