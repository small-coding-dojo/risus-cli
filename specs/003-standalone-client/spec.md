# Feature Specification: Standalone Client Distribution

**Feature Branch**: `003-standalone-client`
**Created**: 2026-05-02
**Status**: Draft
**Input**: User description: "As a player I want to use the client without
having python installed. As a developer I want to give a client application
to the players, which they can use without having python installed."

## Clarifications

### Session 2026-05-02

- Q: Can players launch the client by double-clicking without command-line
  arguments and still connect? → A: Yes — if server address or display name
  are not provided as CLI args, the client prompts for them interactively
  before connecting. CLI args skip the prompts.
- Q: Should the interactive server address prompt suggest a default value? →
  A: A configuration file specifies the default server address and port; the
  prompt pre-fills from this file when present.
- Q: Should the app persist connection parameters for future sessions? →
  A: Yes — on normal exit the client writes the last-used server address and
  display name to the configuration file as new defaults.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download and Run Client (Priority: P1)

A player receives or downloads the Risus client application and can launch it
immediately on their machine without installing Python, pip, or any other
runtime dependencies.

**Why this priority**: Core requirement — the entire feature exists for this
outcome. Without this, nothing else matters.

**Independent Test**: Can be fully tested by downloading the distributed
package, running it on a clean machine with no Python installed, and verifying
the battle manager connects and operates normally.

**Acceptance Scenarios**:

1. **Given** a player has no Python installed, **When** they run the
   distributed client executable, **Then** the Risus battle manager starts
   and functions identically to the Python-based version.
2. **Given** a player double-clicks or runs the executable, **When** the
   application starts, **Then** no error about missing Python or dependencies
   appears.
3. **Given** a player on Windows, macOS, or Linux, **When** they run the
   platform-appropriate package, **Then** the client connects to a running
   Risus server.
4. **Given** a player double-clicks the executable without providing any
   command-line arguments, **When** the application starts, **Then** it
   prompts the player to enter the server address and their display name
   before connecting.
5. **Given** a player launches the executable with server address and name
   as command-line arguments, **When** the application starts, **Then** it
   connects immediately without showing interactive prompts.
6. **Given** a player has connected and then exits the application normally,
   **When** they launch the client again, **Then** the server address and
   display name prompts are pre-filled with the values from the previous
   session.

---

### User Story 2 - Developer Builds and Distributes Client (Priority: P2)

A developer can produce a distributable package from the project source for
each supported platform and hand it to players as a single file or archive.

**Why this priority**: Without a reliable build process, the player-facing
outcome cannot be delivered or updated.

**Independent Test**: Can be fully tested by a developer running a single
build command and inspecting the output artifact — verifying it exists, is
self-contained, and runs on a target machine without a Python environment.

**Acceptance Scenarios**:

1. **Given** a developer has the project checked out and dev dependencies
   installed, **When** they run the build command, **Then** a distributable
   artifact is produced in a known output directory.
2. **Given** a freshly produced artifact, **When** it is copied to a machine
   without Python and executed, **Then** it runs without errors.
3. **Given** the project source changes, **When** the developer rebuilds,
   **Then** the updated artifact reflects the changes.

---

### User Story 3 - Clear Download Instructions for Players (Priority: P3)

Players can find instructions on where to get the client and how to run it,
without needing to read Python packaging documentation.

**Why this priority**: Reduces friction and support requests; players should
not need to understand the build toolchain.

**Independent Test**: Can be tested independently by following only the
player-facing instructions from start to finish on a clean machine.

**Acceptance Scenarios**:

1. **Given** a player reads the player-facing documentation, **When** they
   follow the steps, **Then** they can run the client without any prior
   technical knowledge about Python.
2. **Given** the distributed package is available, **When** a player downloads
   and extracts it, **Then** clear run instructions are present (README or
   similar) alongside the executable.

---

### Edge Cases

- What happens when a player's OS blocks unsigned executables (e.g., macOS
  Gatekeeper, Windows SmartScreen)?
- How does the client handle a missing or unreachable server when launched as
  a standalone binary?
- What happens if the player runs an outdated client against a newer server
  version?
- What happens if the player presses Enter with an empty server address or
  display name in the interactive prompt? (FR-010: re-prompt until non-empty)
- What happens if the player provides a server address via CLI but omits the
  display name (or vice versa)? The missing argument triggers a prompt for
  the omitted value only.
- What happens if the configuration file is present but contains an invalid
  or malformed server address? The client shows the raw value as the default
  hint; connection failure is reported at connect time, not at prompt time.
- What happens if the configuration file is missing? Server address prompt
  shows no default; player types the address manually.
- What happens if writing the config file on exit fails (read-only
  filesystem, no write permission)? The application closes normally without
  reporting an error; saving is best-effort (FR-013).
- What happens if the application is killed forcefully (SIGKILL, Task
  Manager)? The on-exit save does not run; previously saved defaults are
  retained from the last successful write.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The distributed package MUST run on the target platform without
  requiring Python or any Python package manager to be installed.
- **FR-002**: The distributed package MUST include all runtime dependencies
  bundled inside it.
- **FR-003**: The client's behavior and feature set MUST be identical to the
  Python-source version.
- **FR-004**: The build process MUST be reproducible via a single documented
  command.
- **FR-005**: The build process MUST produce platform-appropriate artifacts
  for each supported platform (Windows, macOS, Linux).
- **FR-006**: Players MUST receive clear instructions on how to download and
  run the client.
- **FR-007**: The distributed package MUST display a meaningful error message
  if the server is unreachable, rather than a raw Python traceback.
- **FR-008**: When launched without command-line arguments, the client MUST
  interactively prompt the player for the server address and their display
  name before attempting to connect. Both prompts MUST pre-fill defaults
  from the configuration file when values are present.
- **FR-011**: The client MUST read a configuration file from a well-known
  location to obtain the default server address, port, and display name. If
  no configuration file is present, prompts show no defaults.
- **FR-012**: Players MUST be able to edit the configuration file manually
  (plain text) to set their preferred default server address, port, and
  display name without launching the client.
- **FR-013**: On normal exit, the client MUST write the last-used server
  address and display name to the configuration file. If the write fails
  (e.g., read-only filesystem), the failure MUST be silently ignored and
  the application MUST still close normally.
- **FR-009**: When launched with server address and display name as
  command-line arguments, the client MUST connect directly without showing
  interactive prompts.
- **FR-010**: If the player provides an empty value for a required prompt
  (server address or display name), the client MUST re-prompt until a
  non-empty value is entered.

### Key Entities

- **Distributable Package**: A self-contained executable or archive for a
  specific platform that runs the Risus client.
- **Build Artifact**: The output of the build process — a file or directory
  ready for distribution.
- **Supported Platform**: Windows, macOS, and Linux desktop environments
  targeted for distribution.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A player with no Python environment can launch the client and
  connect to a server within 2 minutes of receiving the package.
- **SC-002**: The build process completes without manual intervention from a
  single documented command.
- **SC-003**: The distributed client passes all existing functional tests that
  the source-based client passes.
- **SC-004**: Packages are available for all three supported platforms
  (Windows, macOS, Linux).
- **SC-005**: Players report no installation-related support requests
  attributable to missing Python or dependencies.

## Assumptions

- Target platforms are Windows 10+, macOS 12+, and mainstream Linux
  distributions (Ubuntu 22.04+, Fedora 38+).
- The client does not require system-level privileges (no admin/root needed
  to run).
- The server continues to run as a Python process; only the client side is
  packaged as a standalone binary.
- Network connectivity is required for the client to operate; offline mode is
  out of scope.
- Automatic update distribution is out of scope for this feature; players
  download new versions manually.
- Code signing and notarization for OS security gatekeeping is out of scope
  for the initial version, but players will be informed of any manual trust
  steps needed.
- The configuration file stores connection defaults only (server address,
  port, and display name) — not battle state. The client both reads and
  writes this file. This is distinct from the local persistence prohibition
  in the project constitution, which explicitly targets battle state I/O.
  Planning phase must confirm this interpretation or raise a minor
  constitution amendment.
- Configuration file format is plain text (key=value) so players can edit
  it with any text editor on any platform.
- Configuration file location is same directory as the running executable
  (project root when running from source); exact path resolution is a
  planning decision.
