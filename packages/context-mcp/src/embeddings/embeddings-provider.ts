/**
 * Embeddings Provider Shim for Context-MCP
 *
 * This wraps Continue's TransformersJsEmbeddingsProvider with customized
 * environment settings for context-mcp:
 * - Enables remote model downloads from HuggingFace
 * - Sets persistent cache directory for model files
 *
 * The model (~24MB all-MiniLM-L6-v2) is downloaded on first use and cached.
 *
 * @see docs/BUNDLING_SOLUTION.md for architecture details
 */

import path from 'node:path';
import os from 'node:os';
import fs from 'node:fs';
import type { ILLM } from '@continuedev/core';

// Cache directory for embedding models
const CACHE_DIR = path.join(os.homedir(), '.cache', 'context-mcp', 'models');

// Singleton instance for the embeddings provider
let embeddingsProviderInstance: ILLM | null = null;
let initializationPromise: Promise<ILLM> | null = null;

/**
 * EmbeddingsPipeline creates and caches the transformers.js pipeline.
 * We override Continue's default to allow remote model downloads.
 */
class EmbeddingsPipeline {
  static task: string = 'feature-extraction';
  static model: string = 'Xenova/all-MiniLM-L6-v2'; // HuggingFace model ID
  static instance: unknown = null;

  static async getInstance(): Promise<unknown> {
    if (EmbeddingsPipeline.instance !== null) {
      return EmbeddingsPipeline.instance;
    }

    // Dynamically import transformers.js from Continue's vendor module
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore - vendored module path without type declarations
    const { env, pipeline } = await import(
      '@continuedev/core/dist/vendor/modules/@xenova/transformers/src/transformers.js'
    );

    // Configure environment for remote model downloads
    env.allowRemoteModels = true; // Enable HuggingFace downloads
    env.allowLocalModels = true; // Also check local cache
    env.cacheDir = CACHE_DIR; // Persistent cache location
    env.useFSCache = true; // Use filesystem cache

    // Ensure cache directory exists
    if (!fs.existsSync(CACHE_DIR)) {
      fs.mkdirSync(CACHE_DIR, { recursive: true });
    }

    console.error(`[embeddings] Initializing pipeline with model: ${EmbeddingsPipeline.model}`);
    console.error(`[embeddings] Cache directory: ${CACHE_DIR}`);

    EmbeddingsPipeline.instance = await pipeline(
      EmbeddingsPipeline.task,
      EmbeddingsPipeline.model
    );

    console.error('[embeddings] Pipeline initialized successfully');
    return EmbeddingsPipeline.instance;
  }
}

/**
 * Custom embeddings provider that implements ILLM interface.
 * Only the embed() method is required for vector indexing.
 */
export class ContextMcpEmbeddingsProvider {
  // Required ILLM properties
  readonly model: string = 'all-MiniLM-L6-v2';
  readonly embeddingId: string = 'transformers.js::all-MiniLM-L6-v2';
  readonly maxEmbeddingChunkSize: number = 512;
  readonly maxEmbeddingBatchSize: number = 32;

  // Internal state
  private initialized: boolean = false;

  /**
   * Generate embeddings for an array of text chunks.
   * This is the core method required by LanceDbIndex.
   */
  async embed(chunks: string[]): Promise<number[][]> {
    if (chunks.length === 0) {
      return [];
    }

    const extractor = await EmbeddingsPipeline.getInstance();
    if (!extractor) {
      throw new Error('Embeddings pipeline failed to initialize');
    }

    const outputs: number[][] = [];

    // Process chunks one at a time to avoid memory issues
    // all-MiniLM-L6-v2 produces 384-dimensional embeddings
    for (const chunk of chunks) {
      // @ts-expect-error - pipeline returns tensor-like object
      const output = await extractor([chunk], {
        pooling: 'mean',
        normalize: true,
      });

      // Convert tensor to array
      outputs.push(...output.tolist());

      // Small delay to avoid blocking the event loop
      await new Promise((resolve) => setTimeout(resolve, 5));
    }

    return outputs;
  }

  // Stub methods required by ILLM interface but not used for embeddings
  get providerName(): string {
    return 'transformers.js';
  }

  get uniqueId(): string {
    return this.embeddingId;
  }

  get contextLength(): number {
    return 512;
  }

  get completionOptions(): Record<string, unknown> {
    return {};
  }

  async complete(): Promise<string> {
    throw new Error('ContextMcpEmbeddingsProvider does not support text completion');
  }

  async *streamComplete(): AsyncGenerator<string> {
    throw new Error('ContextMcpEmbeddingsProvider does not support text completion');
  }

  async *streamFim(): AsyncGenerator<string> {
    throw new Error('ContextMcpEmbeddingsProvider does not support FIM');
  }

  async *streamChat(): AsyncGenerator<unknown> {
    throw new Error('ContextMcpEmbeddingsProvider does not support chat');
  }

  async chat(): Promise<unknown> {
    throw new Error('ContextMcpEmbeddingsProvider does not support chat');
  }

  async rerank(): Promise<number[]> {
    throw new Error('ContextMcpEmbeddingsProvider does not support reranking');
  }

  countTokens(): number {
    return 0;
  }

  supportsImages(): boolean {
    return false;
  }

  supportsCompletions(): boolean {
    return false;
  }

  supportsPrefill(): boolean {
    return false;
  }

  supportsFim(): boolean {
    return false;
  }

  async listModels(): Promise<string[]> {
    return [this.model];
  }

  renderPromptTemplate(): string {
    return '';
  }
}

/**
 * Get or create the embeddings provider singleton.
 * Thread-safe initialization with promise caching.
 */
export async function getEmbeddingsProvider(): Promise<ILLM> {
  if (embeddingsProviderInstance) {
    return embeddingsProviderInstance;
  }

  if (initializationPromise) {
    return initializationPromise;
  }

  initializationPromise = (async () => {
    const provider = new ContextMcpEmbeddingsProvider();
    // Warm up the pipeline
    await provider.embed(['warmup']);
    embeddingsProviderInstance = provider as unknown as ILLM;
    return embeddingsProviderInstance;
  })();

  return initializationPromise;
}

export default ContextMcpEmbeddingsProvider;
