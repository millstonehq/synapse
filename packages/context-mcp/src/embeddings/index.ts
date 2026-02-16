/**
 * Embeddings module for Context-MCP
 *
 * Provides semantic search capabilities using:
 * - TransformersJS embeddings (all-MiniLM-L6-v2)
 * - LanceDB vector storage and ANN search
 */

export { ContextMcpEmbeddingsProvider, getEmbeddingsProvider } from './embeddings-provider.js';
export {
  getLanceDbIndex,
  buildVectorIndex,
  vectorSearch,
  isVectorSearchAvailable,
} from './vector-index.js';
