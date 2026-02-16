import * as path from 'path';
import { generateHomepage } from '../lib/homepage.js';

interface IndexOptions {
  contentDir?: string;
  output?: string;
}

/**
 * Generate the index.md homepage
 */
export async function index(options: IndexOptions = {}): Promise<void> {
  const {
    contentDir = path.resolve(process.cwd(), 'content'),
    output
  } = options;

  const outputPath = output
    ? path.resolve(process.cwd(), output)
    : path.join(contentDir, 'index.md');

  await generateHomepage({
    contentDir,
    outputPath
  });
}

/**
 * CLI command handler for index generation
 */
export async function indexCommand(args: {
  dir?: string;
  output?: string;
}): Promise<void> {
  const options: IndexOptions = {
    contentDir: args.dir,
    output: args.output
  };

  await index(options);
}
