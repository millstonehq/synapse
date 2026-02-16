/**
 * CustomHeaderFooter Plugin for Quartz
 *
 * Adds custom header/footer elements and "Edit in CMS" links to documents.
 * This plugin runs during build time only, so edit links never appear in source files.
 */

// Map document types to their CMS collection names
const typeToCollection: Record<string, string> = {
  policy: "policies",
  standard: "standards",
  process: "processes",
  sop: "sops",
  runbook: "runbooks",
  system: "systems",
  adr: "adrs",
  prd: "prds",
  capability: "capabilities",
  tdd: "tdds",
}

export interface CustomHeaderFooterOptions {
  baseUrl?: string
  position?: "top" | "bottom" | "both"
  showIcon?: boolean
  debug?: boolean
  showAuthoringGuide?: boolean
  showHomeLink?: boolean
  showEditInCMS?: boolean
}

const defaultOptions: CustomHeaderFooterOptions = {
  baseUrl: "/edit",
  position: "both",
  showIcon: true,
  showAuthoringGuide: true,
  showHomeLink: true,
  showEditInCMS: true,
}

/**
 * Quartz transformer plugin that adds custom header/footer elements and "Edit in CMS" links
 */
export const CustomHeaderFooter = (userOpts?: CustomHeaderFooterOptions) => {
  const opts = { ...defaultOptions, ...userOpts }

  return {
    name: "CustomHeaderFooter",
    htmlPlugins() {
      return [
        () => {
          return (tree: any, file: any) => {
            try {
              // Error recovery: ensure file and data exist
              if (!file || !file.data) {
                return
              }

              const filePath = file.path || file.history?.[0] || "unknown"

              // Add custom header with navigation links
              const headerNav = {
                type: "element",
                tagName: "nav",
                properties: {
                  className: ["custom-header-nav"],
                  style: "padding: 1rem 0; margin-bottom: 2rem; border-bottom: 2px solid var(--lightgray); display: flex; gap: 1.5rem; align-items: center;"
                },
                children: [
                  ...(opts.showHomeLink ? [{
                    type: "element",
                    tagName: "a",
                    properties: {
                      href: "/",
                      className: ["nav-link"],
                      style: "color: var(--dark); text-decoration: none; font-weight: 600; font-size: 1.1rem;"
                    },
                    children: [{
                      type: "text",
                      value: "🧬 Synapse Docs"
                    }]
                  }] : []),
                  ...(opts.showAuthoringGuide ? [{
                    type: "element",
                    tagName: "a",
                    properties: {
                      href: "/00_Guides/Authoring-Guide",
                      className: ["nav-link"],
                      style: "color: var(--dark); text-decoration: none; font-weight: 500;"
                    },
                    children: [{
                      type: "text",
                      value: "📚 Authoring Guide"
                    }]
                  }] : []),
                  {
                    type: "element",
                    tagName: "a",
                    properties: {
                      href: "/00_Guides/Examples",
                      className: ["nav-link"],
                      style: "color: var(--dark); text-decoration: none; font-weight: 500;"
                    },
                    children: [{
                      type: "text",
                      value: "📝 Examples"
                    }]
                  }
                ]
              }

              // Add custom footer with useful links
              const footerNav = {
                type: "element",
                tagName: "footer",
                properties: {
                  className: ["custom-footer-nav"],
                  style: "padding: 2rem 0; margin-top: 4rem; border-top: 2px solid var(--lightgray); display: flex; flex-wrap: wrap; gap: 2rem; justify-content: space-between; align-items: center;"
                },
                children: [
                  {
                    type: "element",
                    tagName: "div",
                    properties: {
                      style: "display: flex; gap: 1.5rem; flex-wrap: wrap;"
                    },
                    children: [
                      ...(opts.showAuthoringGuide ? [{
                        type: "element",
                        tagName: "a",
                        properties: {
                          href: "/00_Guides/Authoring-Guide",
                          className: ["footer-link"],
                          style: "color: var(--darkgray); text-decoration: none;"
                        },
                        children: [{
                          type: "text",
                          value: "📚 Authoring Guide"
                        }]
                      }] : []),
                      {
                        type: "element",
                        tagName: "a",
                        properties: {
                          href: "/00_Guides/Examples",
                          className: ["footer-link"],
                          style: "color: var(--darkgray); text-decoration: none;"
                        },
                        children: [{
                          type: "text",
                          value: "Examples"
                        }]
                      },
                      {
                        type: "element",
                        tagName: "a",
                        properties: {
                          href: "/edit",
                          className: ["footer-link"],
                          style: "color: var(--darkgray); text-decoration: none;"
                        },
                        children: [{
                          type: "text",
                          value: "Edit in CMS"
                        }]
                      }
                    ]
                  },
                  {
                    type: "element",
                    tagName: "div",
                    properties: {
                      style: "color: var(--gray); font-size: 0.9rem;"
                    },
                    children: [{
                      type: "text",
                      value: "Powered by Synapse Documentation Framework"
                    }]
                  }
                ]
              }

              // Debug logging for TDD files
              if (filePath.includes("tdd") || filePath.includes("TDD")) {
                console.log("Processing TDD file:", filePath)
                console.log("Frontmatter:", file.data?.frontmatter)
              }

              // Check if document has a type in frontmatter for Edit in CMS functionality
              let editLinkElement = null
              let editLinkElementTop = null

              if (opts.showEditInCMS && file.data?.frontmatter) {
                const docType = file.data.frontmatter.type
                if (docType && typeToCollection[docType]) {
                  const collection = typeToCollection[docType]
                  let slug = file.data?.slug || ""

                  if (slug) {
                    // Extract the path relative to collection folder
                    // e.g., "30_Processes/examples/example-change-management-process"
                    //    -> "examples/example-change-management-process"
                    const pathParts = slug.split('/')
                    // Skip the first part (e.g., "30_Processes") to get relative path
                    const relativePath = pathParts.length > 1
                      ? pathParts.slice(1).join('/')
                      : pathParts[0]
                    const editUrl = `/static/edit/#/collections/${collection}/entries/${relativePath}`

                    // Create the edit link element
                    editLinkElement = {
                      type: "element",
                      tagName: "div",
                      properties: {
                        className: ["edit-in-cms"],
                        style: "margin: 2rem 0; padding: 1rem 0; border-top: 1px solid var(--lightgray);"
                      },
                      children: [
                        {
                          type: "element",
                          tagName: "a",
                          properties: {
                            href: "#",
                            "data-cms-url": editUrl,
                            target: "_blank",
                            rel: "noopener noreferrer",
                            className: ["edit-in-cms-link"],
                            onclick: "event.preventDefault(); window.open(this.dataset.cmsUrl, '_blank');",
                            style: "display: inline-flex; align-items: center; padding: 0.5rem 1rem; background-color: var(--lightgray); color: var(--dark); text-decoration: none; border-radius: 6px; font-weight: 500; transition: all 0.2s ease; cursor: pointer;"
                          },
                          children: [
                            ...(opts.showIcon ? [{
                              type: "element",
                              tagName: "svg",
                              properties: {
                                xmlns: "http://www.w3.org/2000/svg",
                                width: "14",
                                height: "14",
                                viewBox: "0 0 24 24",
                                fill: "none",
                                stroke: "currentColor",
                                "stroke-width": "2",
                                "stroke-linecap": "round",
                                "stroke-linejoin": "round",
                                style: "display: inline-block; vertical-align: middle; margin-right: 0.3rem;"
                              },
                              children: [
                                {
                                  type: "element",
                                  tagName: "path",
                                  properties: {
                                    d: "M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
                                  },
                                  children: []
                                },
                                {
                                  type: "element",
                                  tagName: "path",
                                  properties: {
                                    d: "M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
                                  },
                                  children: []
                                }
                              ]
                            }] : []),
                            {
                              type: "element",
                              tagName: "span",
                              properties: {},
                              children: [
                                {
                                  type: "text",
                                  value: "Edit in CMS"
                                }
                              ]
                            }
                          ]
                        }
                      ]
                    }

                    // Create a second edit link element for top position if needed
                    if (opts.position === "both") {
                      editLinkElementTop = JSON.parse(JSON.stringify(editLinkElement))
                      editLinkElementTop.properties.className = ["edit-in-cms", "edit-in-cms-top"]
                      editLinkElementTop.properties.style = "margin: 0 0 2rem 0; padding: 1rem 0; border-bottom: 1px solid var(--lightgray);"
                    }
                  }
                }
              }

              // Add CSS styles
              const styleElement = {
                type: "element",
                tagName: "style",
                properties: {},
                children: [
                  {
                    type: "text",
                    value: `
                      .custom-header-nav .nav-link:hover {
                        color: var(--secondary) !important;
                        text-decoration: underline !important;
                      }
                      .custom-footer-nav .footer-link:hover {
                        color: var(--dark) !important;
                        text-decoration: underline !important;
                      }
                      .edit-in-cms-link:hover {
                        background-color: var(--gray) !important;
                        transform: translateY(-1px);
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                      }
                      :root[saved-theme="dark"] .edit-in-cms-link {
                        background-color: var(--lightgray);
                        color: var(--light);
                      }
                      :root[saved-theme="dark"] .custom-header-nav .nav-link {
                        color: var(--light);
                      }
                      :root[saved-theme="dark"] .custom-footer-nav .footer-link {
                        color: var(--lightgray);
                      }
                      .edit-in-cms-top {
                        margin-top: 0 !important;
                      }
                    `
                  }
                ]
              }

              // Add JavaScript to handle clicks
              const scriptElement = {
                type: "element",
                tagName: "script",
                properties: {},
                children: [
                  {
                    type: "text",
                    value: `
                      document.addEventListener('DOMContentLoaded', function() {
                        document.querySelectorAll('.edit-in-cms-link').forEach(function(link) {
                          link.addEventListener('click', function(e) {
                            e.preventDefault();
                            window.open(this.dataset.cmsUrl, '_blank');
                          });
                        });
                      });
                    `
                  }
                ]
              }

              // Build the tree with all elements
              tree.children = tree.children || []

              // Add header navigation at the very top
              tree.children.unshift(headerNav)

              // Add edit links based on position setting
              if (editLinkElement) {
                if (opts.position === "bottom") {
                  tree.children.push(editLinkElement)
                } else if (opts.position === "top") {
                  tree.children.splice(2, 0, editLinkElement) // After header nav
                } else if (opts.position === "both" && editLinkElementTop) {
                  tree.children.splice(2, 0, editLinkElementTop) // After header nav
                  tree.children.push(editLinkElement) // At bottom
                }
              }

              // Add footer and scripts at the end
              tree.children.push(footerNav)
              tree.children.push(styleElement)
              tree.children.push(scriptElement)

            } catch (error) {
              if (opts.debug) {
                console.error('CustomHeaderFooter plugin error:', error)
              }
            }
          }
        }
      ]
    }
  }
}
