import { encoding_for_model, Tiktoken } from 'tiktoken';

/**
 * Simple token counter using tiktoken
 */
export class TokenCounter {
  private encoder: Tiktoken;

  constructor() {
    // Use GPT-4 encoding as a reasonable default
    this.encoder = encoding_for_model('gpt-4');
  }

  /**
   * Count tokens in text
   */
  count(text: string): number {
    try {
      return this.encoder.encode(text).length;
    } catch (error) {
      // Fallback to rough estimation if encoding fails
      return Math.ceil(text.length / 4);
    }
  }

  /**
   * Free encoder resources
   */
  free(): void {
    this.encoder.free();
  }
}
