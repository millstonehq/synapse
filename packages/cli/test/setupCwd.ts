import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PACKAGE_ROOT = path.resolve(__dirname, '..'); // packages/cli

const ORIGINAL = process.cwd();

beforeEach(() => {
  try {
    process.chdir(PACKAGE_ROOT);
  } catch {}
});

afterEach(() => {
  try {
    process.chdir(PACKAGE_ROOT);
  } catch {}
});

afterAll(() => {
  try {
    process.chdir(ORIGINAL);
  } catch {}
});
