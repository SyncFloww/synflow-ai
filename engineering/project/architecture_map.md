# Engineering OS Architecture Guide

Engineering OS follows a strict modular clean architecture:

- `cli/`: Command-line interface parser, argument validation, and output formatters.
- `commands/`: Individual CLI command handlers with exception handling and exit codes.
- `core/`: Base models (`CommandResult`, `ProjectAnalysis`, `GraphNode`, `HealthReport`), protocols, and exception definitions.
- `execution/`: Task runner, project analyzers, and code repair utilities.
- `orchestration/`: Task planning engine (`Orchestrator`) for orchestrating engineering workflows.
- `plugins/`: Extensible framework inspection plugin architecture (`Django`, `React`, `NestJS`, `Flutter`, `Generic`).
- `graph/`: AST code parser and Knowledge Graph builder (`GraphBuilder`).
- `memory/`: Architectural memory manager (`MemoryManager`).
- `state/`: Persistent state store (`ProjectStateStore`).
- `reporting/`: Repository health, risk, and complexity reporter (`Reporter`).
- `documentation/`: Documentation generator (`DocGenerator`).
- `utils/`: Common path traversers, AST utilities, and formatting helpers.
