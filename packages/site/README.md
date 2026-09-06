# Synapse Documentation Site (Quartz 4)

This directory contains configuration files for Quartz 4 static site generator, which is integrated as a git submodule for the Synapse Documentation Framework.

## Architecture

Quartz 4 is included as a git submodule at `site/quartz/`. This approach:
- Keeps Quartz updates manageable via git submodule commands
- Maintains clear separation between Synapse and Quartz code
- Allows version pinning to specific Quartz releases
- Enables easy rollback if needed

## Setup

### Prerequisites
- Node.js v20+ (v22+ preferred)
- npm v10+
- Git

### Initial Setup

From the project root:

```bash
# Install site dependencies
cd site
npm install

# Run the setup script (TypeScript)
npm run setup
```

The setup script will:
1. Initialize the Quartz submodule if not present
2. Install Quartz dependencies
3. Copy our configuration files into Quartz
4. Create a symlink from `quartz/content` to `../../content`

### Manual Setup (if needed)

```bash
# From project root
git submodule add -b v4 https://github.com/jackyzha0/quartz.git site/quartz
cd site/quartz
npm install

# Copy configurations
cp ../quartz.config.ts .
cp ../quartz.layout.ts .

# Link content
rm -rf content
ln -s ../../content content
```

## Development

### Start Development Server

```bash
# From site directory
npm run dev

# Or directly from quartz directory
cd site/quartz
npx quartz build --serve
```

The site will be available at `http://localhost:8080` with hot reload enabled.

### Available Scripts

From the `site/` directory:

- `npm run setup` - Initialize and configure Quartz submodule
- `npm run build` - Build the static site
- `npm run serve` - Build and serve locally
- `npm run dev` - Development server with hot reload
- `npm run update-submodule` - Update Quartz to latest version
- `npm run clean` - Clean build artifacts

## Configuration Files

### `quartz.config.ts`
Main Quartz configuration with:
- Site title and metadata
- Theme and color scheme
- Plugin configuration
- Graph, backlinks, and tags enabled
- Obsidian-flavored markdown support

### `quartz.layout.ts`
Layout configuration defining:
- Graph component in right sidebar (interactive, zoomable)
- Backlinks below the graph
- Tags in article headers
- Search and explorer in left sidebar
- Table of contents positioning

### `custom.scss` (optional)
Custom styles for:
- Document type badges
- Status indicators
- Enhanced graph styling
- Responsive design adjustments

## Features Configured

✅ **Graph Visualization**
- Local graph: 2-level depth from current document
- Global graph: Full documentation network
- Interactive drag, zoom, and hover
- Tags shown on nodes

✅ **Automatic Backlinks**
- Shows documents that reference the current page
- Positioned below the graph in right sidebar

✅ **Tag Navigation**
- Tags displayed in article headers
- Dedicated tag index pages
- Tag-based content discovery

✅ **Additional Features**
- Full-text search
- Dark/light theme toggle
- Breadcrumb navigation
- Table of contents
- Obsidian wikilink support

## Building for Production

```bash
# Build the static site
cd site
npm run build

# Output will be in site/quartz/public/
```

The `public/` directory can be deployed to any static hosting service:
- GitHub Pages
- Netlify
- Vercel
- AWS S3 + CloudFront
- Any web server

## Updating Quartz

To update to the latest Quartz v4:

```bash
cd site
npm run update-submodule

# Re-run setup to apply our configurations
npm run setup
```

## Troubleshooting

### Submodule not initialized
```bash
git submodule update --init --recursive
```

### Content not appearing
- Check symlink: `ls -la site/quartz/content`
- Should point to `../../content`
- Verify files have proper YAML frontmatter

### Build errors
- Ensure Node v20+ with `node --version`
- Run `npm install` in both `site/` and `site/quartz/`
- Check frontmatter syntax is valid YAML

### Permission errors on setup
```bash
chmod +x site/setup-quartz.ts
```

## Integration with Synapse

The Quartz site automatically processes all content in the Synapse vault:
- Documents in numbered folders (10_Policies, 20_Standards, etc.)
- Templates and schemas (excluded from build)
- Examples generated from YAML seeds
- All cross-references via wikilinks

The graph visualization will show the relationships between:
- Processes and their standards
- SOPs and their parent processes
- Runbooks and their systems
- ADRs and their related documents
### Public example site

The repository's GitHub Pages workflow builds with `SYNAPSE_EXAMPLES_ONLY=true`.
This stages only Markdown under an `examples/` directory with boolean
`example: true` frontmatter, excluding `draft: true`. It generates a demo landing
page and builds the CMS document index from that same staged content. Raw vault
assets, symlinks, and other documents are excluded. Keep any future public assets
in an explicitly reviewed publication path before extending this allowlist.
Normal builds without this environment variable continue to render the full vault.

GitHub Pages settings are managed by Mill's `XGitHubRepository/synapse` resource;
GitHub Actions builds and deploys the site at https://millstonehq.github.io/synapse/.
