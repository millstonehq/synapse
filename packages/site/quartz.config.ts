import { QuartzConfig } from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"
import { CustomHeaderFooter } from "./plugins/CustomHeaderFooter"

/**
 * Quartz 4 Configuration for Synapse Documentation Framework
 *
 * This file should be copied into the Quartz submodule root after initialization.
 * The configuration enables graph visualization, backlinks, and tags as required
 * by SYN-P1-T02.
 *
 * Environment overrides (used in CI for GitHub Pages deployment):
 *   QUARTZ_BASE_URL - e.g. "millstonehq.github.io/synapse"
 */
const baseUrl = process.env.QUARTZ_BASE_URL ?? "synapse.local"

const config: QuartzConfig = {
  configuration: {
    pageTitle: "🧬 Synapse Documentation",
    enableSPA: true,
    enablePopovers: true,
    analytics: null,
    locale: "en-US",
    baseUrl,
    ignorePatterns: ["private", "templates", ".obsidian", "_assets", "examples/*.yaml"],
    defaultDateType: "created",
    theme: {
      fontOrigin: "googleFonts",
      cdnCaching: true,
      typography: {
        header: "Schibsted Grotesk",
        body: "Source Sans Pro",
        code: "IBM Plex Mono",
      },
      colors: {
        lightMode: {
          light: "#faf8f8",
          lightgray: "#e5e5e5",
          gray: "#b8b8b8",
          darkgray: "#4e4e4e",
          dark: "#2b2b2b",
          secondary: "#284b63",
          tertiary: "#84a59d",
          highlight: "rgba(143, 159, 169, 0.15)",
          textHighlight: "#fff23688",
        },
        darkMode: {
          light: "#161618",
          lightgray: "#393639",
          gray: "#646464",
          darkgray: "#d4d4d4",
          dark: "#ebebec",
          secondary: "#7b97aa",
          tertiary: "#84a59d",
          highlight: "rgba(143, 159, 169, 0.15)",
          textHighlight: "#b3aa0288",
        },
      },
    },
  },
  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({
        priority: ["frontmatter", "filesystem"],
      }),
      ...(process.env.SYNAPSE_EXAMPLES_ONLY === "true" ? [] : [CustomHeaderFooter({
        baseUrl: "/edit",
        position: "both",
        showIcon: true,
        showAuthoringGuide: true,
        showHomeLink: true,
        showEditInCMS: true,
      }) as any]), // The public demo uses Quartz navigation without vault-specific links.
      Plugin.SyntaxHighlighting({
        theme: {
          light: "github-light",
          dark: "github-dark",
        },
        keepBackground: false,
      }),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlEmbed: false }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents({
        maxDepth: 3,
        minEntries: 1,
        showByDefault: true,
        collapseByDefault: false,
      }),
      Plugin.CrawlLinks({ markdownLinkResolution: "shortest" }),
      Plugin.Description(),
      Plugin.Latex({ renderEngine: "katex" }),
    ],
    filters: [Plugin.RemoveDrafts()],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({
        enableSiteMap: true,
        enableRSS: true,
      }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.NotFoundPage(),
    ],
  },
}

export default config
