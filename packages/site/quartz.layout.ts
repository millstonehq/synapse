import { PageLayout, SharedLayout } from "./quartz/cfg"
import * as Component from "./quartz/components"

/**
 * Quartz Layout Configuration for Synapse Documentation Framework
 * 
 * This file configures the positioning of graph, backlinks, and tags components
 * as required by SYN-P1-T02.
 */

// Components shared across all pages
export const sharedPageComponents: SharedLayout = {
  head: Component.Head(),
  header: [],
  afterBody: [],
  footer: Component.Footer({
    links: {
      "GitHub": "https://github.com/your-org/synapse",
      "Obsidian": "obsidian://open?vault=synapse",
    },
  }),
}

// Layout for list pages (folders, tags, etc.)
export const defaultListPageLayout: PageLayout = {
  beforeBody: [
    Component.Breadcrumbs(),
    Component.ArticleTitle(),
    Component.ContentMeta(),
  ],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Search(),
    Component.Darkmode(),
    Component.DesktopOnly(Component.Explorer()),
  ],
  right: [
    Component.DesktopOnly(Component.Graph({
      localGraph: {
        drag: true,
        zoom: true,
        depth: 2,
        scale: 1.1,
        repelForce: 0.5,
        centerForce: 0.3,
        linkDistance: 30,
        fontSize: 0.6,
        opacityScale: 1,
        showTags: true,
        removeTags: [],
        focusOnHover: true,
      },
      globalGraph: {
        drag: true,
        zoom: true,
        depth: -1,
        scale: 0.9,
        repelForce: 0.5,
        centerForce: 0.3,
        linkDistance: 30,
        fontSize: 0.5,
        opacityScale: 1,
        showTags: true,
        removeTags: [],
        focusOnHover: true,
      },
    })),
    Component.DesktopOnly(Component.TableOfContents()),
  ],
}

// Layout for individual content pages
export const defaultContentPageLayout: PageLayout = {
  beforeBody: [
    Component.Breadcrumbs(),
    Component.ArticleTitle(),
    Component.ContentMeta(),
    Component.TagList(), // Tags displayed prominently on content pages
  ],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Search(),
    Component.Darkmode(),
    Component.DesktopOnly(Component.Explorer()),
  ],
  right: [
    // Interactive graph showing connections
    Component.Graph({
      localGraph: {
        drag: true,
        zoom: true,
        depth: 2,
        scale: 1.1,
        repelForce: 0.5,
        centerForce: 0.3,
        linkDistance: 30,
        fontSize: 0.6,
        opacityScale: 1,
        showTags: true,
        removeTags: [],
        focusOnHover: true,
      },
      globalGraph: {
        drag: true,
        zoom: true,
        depth: -1,
        scale: 0.9,
        repelForce: 0.5,
        centerForce: 0.3,
        linkDistance: 30,
        fontSize: 0.5,
        opacityScale: 1,
        showTags: true,
        removeTags: [],
        focusOnHover: true,
      },
    }),
    Component.DesktopOnly(Component.TableOfContents()),
    // Automatic backlinks showing documents that reference this one
    Component.Backlinks(),
  ],
}