# Documentation Framework Plugin

Comprehensive documentation authoring framework with skills and agents for Obsidian vault optimization, content curation, knowledge graph management, and automated documentation generation.

## Features

### 📊 Skills (Base)

#### Data Model Visualizer
Create ER diagrams and data flow visualizations from discovered schemas using Mermaid syntax.

**Use Cases:**
- Visualizing database relationships
- Creating entity-relationship diagrams
- Mapping data flows between systems
- Documenting data models

**Outputs:** Mermaid ER diagrams, data flow diagrams, class diagrams

#### System Mapper
Synthesize discovered information into comprehensive system documentation including architecture diagrams, integration maps, and data flows.

**Use Cases:**
- After API/schema discovery is complete
- Creating complete system documentation packages
- Documenting architecture and integrations
- Mapping workflows and deployment topology

**Outputs:** Multi-document system documentation with architecture diagrams, data models, integration maps, workflows, security analysis

### 🤖 Agents (Base)

#### Connection Agent
Analyzes and suggests links between related content, identifies orphaned notes, and creates knowledge graph connections.

**Capabilities:**
- Entity-based connection discovery
- Keyword overlap analysis
- Orphaned note detection
- Link suggestion generation

#### Content Curator
Identifies outdated content, suggests improvements, consolidates similar notes, and maintains content quality standards.

**Capabilities:**
- Content quality assessment
- Duplicate detection and consolidation
- Content enhancement suggestions
- Relevance analysis

#### Metadata Agent
Ensures consistent frontmatter metadata across the vault with standardized tags, types, and dates.

**Capabilities:**
- Frontmatter standardization
- Automatic metadata addition
- Tag generation from directory structure
- File type classification

#### MOC Agent
Identifies and generates missing Maps of Content (MOCs), organizes orphaned assets, and maintains navigation structure.

**Capabilities:**
- MOC generation and updates
- Orphaned image organization
- Gallery note creation
- Navigation structure maintenance

#### Review Agent
Cross-checks enhancement work, validates consistency, and ensures quality across the vault.

**Capabilities:**
- Metadata consistency verification
- Link quality validation
- Tag standardization checks
- MOC completeness assessment

#### Tag Agent
Normalizes and hierarchically organizes tag taxonomy, consolidates duplicates, and maintains consistent tagging.

**Capabilities:**
- Technology name normalization
- Hierarchical tag structure application
- Duplicate tag consolidation
- Taxonomy maintenance

#### Vault Optimizer
Analyzes vault performance, optimizes file sizes, manages large attachments, and improves search indexing.

**Capabilities:**
- Performance analysis
- File size optimization
- Attachment management
- Storage cleanup

## Installation

```bash
# Install from the Synapse marketplace
/plugin marketplace add https://github.com/millstonehq/synapse
/plugin install docs@synapse

# Core plugin is required (automatically installed as dependency)
```

## Directory Structure

```
plugins/docs/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── skills/
│   ├── base/                # Base skills (version controlled)
│   │   ├── data-model-visualizer/
│   │   └── system-mapper/
│   └── custom/              # Your custom skills (gitignored)
├── agents/
│   ├── base/                # Base agents (version controlled)
│   │   ├── connection-agent.md
│   │   ├── content-curator.md
│   │   ├── metadata-agent.md
│   │   ├── moc-agent.md
│   │   ├── review-agent.md
│   │   ├── tag-agent.md
│   │   └── vault-optimizer.md
│   └── custom/              # Your custom agents (gitignored)
└── README.md
```

## Customization

### Adding Custom Skills

Place your organization-specific skills in `skills/custom/`:

```bash
plugins/docs/skills/custom/
└── my-custom-visualizer/
    └── SKILL.md
```

Custom skills are automatically discovered and will not be overwritten during plugin updates.

### Adding Custom Agents

Place your organization-specific agents in `agents/custom/`:

```bash
plugins/docs/agents/custom/
└── my-custom-agent.md
```

Custom agents are automatically loaded alongside base agents.

## Usage

### Using Skills

Skills are invoked with the `/skill` command:

```bash
# Invoke the data model visualizer
/skill data-model-visualizer

# Invoke the system mapper
/skill system-mapper
```

### Using Agents

Agents are specialized subagents that Claude Code will proactively use when their capabilities match your task:

- **Connection Agent**: Automatically used when analyzing note relationships
- **Content Curator**: Used proactively for content quality improvements
- **Metadata Agent**: Used when standardizing frontmatter
- **MOC Agent**: Used when organizing navigation structure
- **Review Agent**: Used for quality assurance checks
- **Tag Agent**: Used for tag taxonomy management
- **Vault Optimizer**: Used for performance optimization

## Requirements

- **Core Plugin**: Required (automatically installed as dependency)
- **Obsidian**: For vault management features
- **Python 3**: For some agent scripts (optional)

## Documentation Framework Workflow

1. **Initialize** documentation structure with `/synapse init`
2. **Author** content following the Synapse documentation framework
3. **Enhance** with agents (metadata, connections, tags)
4. **Visualize** data models and systems with skills
5. **Optimize** vault performance regularly
6. **Review** and maintain quality standards

## License

MIT

## Support

For issues, questions, or contributions:
- GitHub: https://github.com/millstonehq/synapse
- Documentation: See `content/70_Systems/synapse-documentation-framework.md`
