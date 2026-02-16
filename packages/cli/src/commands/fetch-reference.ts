import { JSDOM } from "jsdom"
import { Readability } from "@mozilla/readability"
import TurndownService from "turndown"

export interface FetchReferenceResult {
  markdown: string
  title: string
  byline: string | null
  excerpt: string | null
  url: string
}

/**
 * Fetch a URL and convert it to markdown using Mozilla Readability + Turndown
 */
export async function fetchReference(
  url: string,
): Promise<FetchReferenceResult> {
  try {
    // Validate URL
    let parsedUrl: URL
    try {
      parsedUrl = new URL(url)
    } catch (error) {
      throw new Error(`Invalid URL: ${url}`)
    }

    // Fetch the HTML
    const response = await fetch(url, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (compatible; SynapseBot/1.0; +https://github.com/your-org/synapse)",
      },
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch ${url}: ${response.status} ${response.statusText}`)
    }

    const html = await response.text()

    // Parse with JSDOM
    // Note: We don't need CSS parsing - Readability analyzes DOM structure, not styles
    const dom = new JSDOM(html, {
      url,
      // Don't parse stylesheets or load external resources
      // This avoids CSS parsing errors with modern syntax
      pretendToBeVisual: false,
    })

    // Extract main content with Readability
    const reader = new Readability(dom.window.document)
    const article = reader.parse()

    if (!article) {
      throw new Error(`Failed to extract readable content from ${url}`)
    }

    // Convert HTML to Markdown with Turndown
    const turndownService = new TurndownService({
      headingStyle: "atx",
      codeBlockStyle: "fenced",
      bulletListMarker: "-",
    })

    // Add custom rules for better markdown conversion
    turndownService.addRule("strikethrough", {
      filter: ["del", "s"],
      replacement: (content: string) => `~~${content}~~`,
    })

    const markdown = turndownService.turndown(article.content || "")

    return {
      markdown,
      title: article.title || "Untitled",
      byline: article.byline || null,
      excerpt: article.excerpt || null,
      url: parsedUrl.toString(),
    }
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Error fetching reference from ${url}: ${error.message}`)
    }
    throw error
  }
}

/**
 * CLI command handler for fetch-reference
 */
export async function fetchReferenceCommand(args: {
  url?: string
  [key: string]: any
}): Promise<void> {
  const { url } = args

  if (!url) {
    console.error("Error: URL is required")
    console.error("Usage: synapse fetch-reference <url>")
    process.exit(1)
  }

  try {
    const result = await fetchReference(url)

    // Output as JSON for easy parsing by slash commands
    console.log(JSON.stringify(result, null, 2))
  } catch (error) {
    if (error instanceof Error) {
      console.error(`Error: ${error.message}`)
    } else {
      console.error("An unexpected error occurred")
    }
    process.exit(1)
  }
}
