# Feature Specification: Secure Session

**Feature Branch**: `004-secure-session`
**Created**: 2026-05-03
**Status**: Draft
**Input**: Shared-secret token access control and encrypted transit for public
server deployments

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Authorized Player Connects (Priority: P1)

A player who knows the session token launches the client and connects to the
game server. The server admits them. A player without the token, or with the
wrong one, is denied access with a clear rejection message.

**Why this priority**: Core security gate — without it the feature does not
exist.

**Independent Test**: Start a protected server and attempt connection with
correct, wrong, and absent tokens. Delivers the primary security value on its
own.

**Acceptance Scenarios**:

1. **Given** the server has a session token configured, **When** a player
   connects with the correct token, **Then** the connection is accepted and
   game state is received.
2. **Given** the server has a session token configured, **When** a player
   connects with the wrong token, **Then** the connection is rejected and the
   client re-prompts the player for a new token before retrying.
3. **Given** the server has a session token configured, **When** a player
   connects without providing any token, **Then** the connection is rejected
   and the client re-prompts the player for a token.
4. **Given** the server has **no** session token configured, **When** any
   player attempts to connect, **Then** all connections are rejected.

---

### User Story 2 - Token Remembered Between Sessions (Priority: P2)

A player enters their session token once. On subsequent launches of the client,
they are not prompted again — the stored token is reused automatically.
Entering a new token on next launch overrides the saved one.

**Why this priority**: Eliminates friction for returning players; the prompt is
only an acceptable UX for first-time use.

**Independent Test**: Enter a token, quit, relaunch — observe no prompt and
successful connection. Delivers standalone usability value.

**Acceptance Scenarios**:

1. **Given** no token is stored and `--token` was not passed, **When** the
   client starts, **Then** the player is prompted for a token and cannot
   proceed without entering one.
2. **Given** a token was entered in a previous session, **When** the client
   starts, **Then** the stored token is used automatically and no prompt
   appears.
3. **Given** the player quits the client normally, **When** the client
   restarts, **Then** the token from the previous session is reused without
   prompting.

---

### User Story 3 - Command-Line Token Override (Priority: P3)

An operator or scripter provides the session token as a command-line argument,
bypassing the interactive prompt and the stored value entirely.

**Why this priority**: Enables automation and headless use; lower priority than
interactive flows but required for scripted deployments.

**Independent Test**: Pass `--token` on launch, verify prompt never appears and
the supplied token is used.

**Acceptance Scenarios**:

1. **Given** a `--token` argument is passed on launch, **When** the client
   starts, **Then** no prompt is shown, the supplied token is used for the
   connection, and the token is persisted to `risus.cfg` on clean exit only
   if the connection succeeds; a server-rejected token MUST NOT be saved.
2. **Given** a `--token` argument is passed and a different token is stored in
   config, **When** the client connects, **Then** the command-line token takes
   precedence over the stored one.

---

### User Story 4 - Encrypted Transport for Public Servers (Priority: P4)

When connecting to a server reachable by domain name (public internet), all
communication is encrypted in transit. When connecting to a local address
(host:port), plain communication is used for developer convenience.

**Why this priority**: Prevents credential and game-state exposure over public
networks; domain-name vs. host:port heuristic covers the common deployment
split.

**Independent Test**: Connect to `hostname:port` and to a bare domain name;
confirm the correct protocol is selected in each case.

**Acceptance Scenarios**:

1. **Given** the server address contains a colon (e.g. `localhost:8765`),
   **When** the client builds the connection URI, **Then** an unencrypted
   local protocol is used.
2. **Given** the server address is a bare hostname without a port (e.g.
   `risus.boos.systems`), **When** the client builds the connection URI,
   **Then** an encrypted protocol is used.

---

### Edge Cases

- What happens when the player presses Enter without typing a token at the
  prompt? *(Must re-prompt; empty token not accepted.)*
- What happens when the player enters a token shorter than 16 characters?
  *(Rejected with an informative message; player is re-prompted.)*
- What happens if the stored token was correct yesterday but the server token
  changed? *(Connection is rejected; player must supply the new token
  manually.)*
- What if two clients share the same config and one updates the stored token?
  *(Last write wins; no coordination is required for shared-secret model.)*
- What if the server starts with no token configured?
  *(All connections are rejected — deliberate defense-in-depth: unconfigured
  server is closed, not open.)*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST reject any client connection that does not present
  the configured session token. The client MUST re-prompt the player for a new
  token and retry rather than exiting.
- **FR-002**: System MUST reject all client connections when no session token
  is configured server-side (secure by default).
- **FR-003**: Client MUST prompt the player for a session token on startup when
  no token is stored in configuration and none was supplied via command-line
  argument. An empty response MUST NOT be accepted. The token MUST be at least
  16 printable non-whitespace characters; shorter values MUST be rejected with
  an informative message.
- **FR-004**: Client MUST persist the session token to local configuration on
  exit so subsequent launches do not re-prompt.
- **FR-005**: Client MUST accept a session token supplied as a command-line
  argument (`--token`), which takes precedence over any stored value and
  suppresses the prompt.
- **FR-006**: Client MUST automatically use an encrypted connection protocol
  when the server address is a bare hostname (no colon), and an unencrypted
  protocol when the address is a `host:port` pair.
- **FR-007**: Client MUST include the session token in the connection request
  to the server.
- **FR-008**: Server-side state retrieval (loading saved game data) MUST work
  correctly regardless of whether the active connection uses an encrypted or
  unencrypted protocol.
- **FR-009**: Server MUST log each rejected connection attempt with: timestamp,
  reason (token absent or token mismatch). The token value itself MUST NOT
  appear in any log output.
- **FR-010**: Server MUST impose a minimum 3-second delay before completing
  token validation — regardless of whether the token is valid, invalid, or
  absent — to limit the effectiveness of brute-force probing.

### Key Entities

- **Session Token**: Shared secret known to all authorized players and the
  server. Single value; all players share the same token for a given server
  deployment. Minimum 16 printable non-whitespace characters; no maximum
  length enforced.
- **Client Configuration**: Persistent local file storing the player's
  last-used server address, display name, and session token across launches.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A client with the correct token connects and receives game state
  within 3–4 seconds of the connection attempt (intentional 3-second
  server-side delay for brute-force mitigation; no additional latency beyond
  that delay).
- **SC-002**: 100% of connection attempts with an absent or incorrect token are
  rejected before any game state is transmitted.
- **SC-003**: A player who entered a token once is not prompted again on any
  subsequent launch unless the stored configuration is cleared.
- **SC-004**: Connections to bare-hostname server addresses are always made
  over an encrypted channel; connections to host:port addresses use a local
  channel.
- **SC-005**: All acceptance scenarios defined across User Stories 1–4 pass in
  automated tests: US1 (4 scenarios), US2 (3 scenarios), US3 (2 scenarios),
  US4 (2 scenarios).

## Clarifications

### Session 2026-05-03

- Q: When a connection is rejected (wrong/absent token), what does the client
  do? → A: Re-prompts player for a new token and retries.
- Q: What format constraints apply to the session token? → A: Minimum 16
  printable non-whitespace characters, no maximum length.
- Q: Should the server log unauthorized connection attempts? → A: Yes — log
  each rejection with timestamp and reason (token absent vs. token mismatch);
  never log the token value itself.
- Q: Should a delay be introduced to limit brute-force probing? → A: Yes —
  server imposes a minimum 3-second delay before completing token validation
  for all connections (valid, invalid, or absent token).

## Assumptions

- All players share a single session token; per-player credentials are out of
  scope.
- Token rotation, expiry, and multi-token support are out of scope for this
  version.
- Authentication for REST endpoints (`/state`, `/saves`, `/healthz`) is out of
  scope.
- The server operator is responsible for distributing the shared token
  out-of-band (e.g., a private message or secure note).
- The TLS reverse proxy (Caddy) and its configuration are deployment concerns
  handled alongside this feature but are not part of the client or server
  application logic.
- The constitution's Principle II ("No authentication") must be amended before
  implementation begins; this spec assumes the amendment will be approved.
