# Engineering OS CLI Reference

## Commands

### `engineering status`
Show the current platform engine status, root path, detected framework, and readiness.

### `engineering inspect`
Perform deep semantic analysis of the codebase using framework-specific plugins (Django, React, NestJS, Flutter, Generic).

### `engineering audit`
Refresh project indexes, documentation snapshots, and architectural memory.

### `engineering graph`
Build AST-based semantic knowledge graph (`knowledge_graph.json`) representing symbols, imports, API endpoints, and database models.

### `engineering docs`
Auto-generate and update platform documentation snapshots.

### `engineering test`
Execute pytest test suite against the repository.

### `engineering work <task>`
Orchestrate a feature task through planning, dependency scanning, context collection, and state tracking.

### `engineering continue`
Resume the latest orchestrated work session and display pending milestones.

### `engineering review`
Perform health review of the repository, update risk/complexity scores, and update health status.

### `engineering fix [task]`
Run orchestrator in repair mode to detect and fix broken imports, weak typing, or failing code.

### `engineering feature <name>`
Summarize a feature area and check existing feature implementation plans.

### `engineering plan <feature>`
Create a structured Markdown feature implementation plan under `engineering/project/feature_plans/`.
