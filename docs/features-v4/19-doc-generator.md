# Feature 19: Doc Generator

## Overview
Architecture documentation generator with ADR (Architecture Decision Record) management and C4 model template support.

## Components
- `doc_generator.py` - Documentation generator engine
- `doc_gen_cog.py` - Discord bot commands for doc generation

## Data Models
- `Documentation` - Generated document with type, content, and metadata
- `ADREntry` - Architecture Decision Record entry
- `C4Model` - C4 model container structure

## Document Types
- **ADR** - Architecture Decision Records with status tracking
- **C4 Context** - System context diagrams
- **C4 Container** - Container-level architecture
- **C4 Component** - Component-level architecture

## CLI Commands
- `ipilot docgen list` - List documents
- `ipilot docgen generate` - Generate a document
- `ipilot docgen get` - Get document content
- `ipilot docgen summary` - Document statistics
