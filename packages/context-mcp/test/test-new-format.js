#!/usr/bin/env node

/**
 * Test script for new file_search response format
 * Tests:
 * - line_number → line_range [start, end]
 * - line_content → content
 * - include_content parameter (default false)
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const serverPath = join(__dirname, 'dist', 'index.js');

async function sendRequest(request) {
  return new Promise((resolve, reject) => {
    const server = spawn('node', [serverPath], {
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let output = '';
    let errorOutput = '';

    server.stdout.on('data', (data) => {
      output += data.toString();
    });

    server.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    server.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Server exited with code ${code}\nError: ${errorOutput}`));
      } else {
        try {
          // Parse JSON-RPC responses
          const lines = output.split('\n').filter(line => line.trim());
          const responses = lines.map(line => {
            try {
              return JSON.parse(line);
            } catch (e) {
              return null;
            }
          }).filter(r => r && r.result);

          resolve(responses);
        } catch (e) {
          reject(new Error(`Failed to parse output: ${e.message}\nOutput: ${output}`));
        }
      }
    });

    // Send initialize
    const init = {
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: { name: 'test', version: '1.0.0' }
      }
    };

    // Send request
    server.stdin.write(JSON.stringify(init) + '\n');
    server.stdin.write(JSON.stringify(request) + '\n');
    server.stdin.end();
  });
}

async function runTests() {
  console.log('🧪 Testing new file_search response format\n');

  // Test 1: Default (include_content: false)
  console.log('Test 1: Default behavior (include_content not specified)');
  try {
    const responses = await sendRequest({
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/call',
      params: {
        name: 'file_search',
        arguments: {
          pattern: 'FileSearchResult',
          mode: 'content',
          max_results: 3
        }
      }
    });

    const result = JSON.parse(responses.find(r => r.id === 2)?.result?.content?.[0]?.text || '{}');

    if (result.results && result.results.length > 0) {
      const firstResult = result.results[0];
      console.log('✅ Result structure:', JSON.stringify(firstResult, null, 2));

      // Verify new format
      if (Array.isArray(firstResult.line_range)) {
        console.log('✅ line_range is array:', firstResult.line_range);
      } else {
        console.log('❌ line_range is NOT an array');
      }

      if (!firstResult.content) {
        console.log('✅ content not included (default behavior)');
      } else {
        console.log('❌ content included when it should not be');
      }
    }
  } catch (error) {
    console.log('❌ Test 1 failed:', error.message);
  }

  console.log('\n');

  // Test 2: Explicit include_content: true
  console.log('Test 2: With include_content: true');
  try {
    const responses = await sendRequest({
      jsonrpc: '2.0',
      id: 3,
      method: 'tools/call',
      params: {
        name: 'file_search',
        arguments: {
          pattern: 'FileSearchResult',
          mode: 'content',
          max_results: 3,
          include_content: true
        }
      }
    });

    const result = JSON.parse(responses.find(r => r.id === 3)?.result?.content?.[0]?.text || '{}');

    if (result.results && result.results.length > 0) {
      const firstResult = result.results[0];
      console.log('✅ Result structure:', JSON.stringify(firstResult, null, 2));

      if (firstResult.content) {
        console.log('✅ content field present');
        console.log('   Content preview:', firstResult.content.substring(0, 100) + '...');
      } else {
        console.log('❌ content field missing when include_content: true');
      }
    }
  } catch (error) {
    console.log('❌ Test 2 failed:', error.message);
  }

  console.log('\n✅ Tests complete!');
}

runTests().catch(console.error);
