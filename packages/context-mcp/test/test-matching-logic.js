#!/usr/bin/env node

// Simulate the fix: finding the matching line within a chunk
function findMatchingLine(chunkContent, searchPattern, chunkStartLine) {
  const lines = chunkContent.split('\n');
  const pattern = searchPattern.toLowerCase();

  let matchingLineIndex = 0;
  let matchingLineContent = lines[0];

  // Search for the pattern in the chunk
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].toLowerCase().includes(pattern)) {
      matchingLineIndex = i;
      matchingLineContent = lines[i];
      break;
    }
  }

  return {
    line_number: chunkStartLine + matchingLineIndex,
    line_content: matchingLineContent,
    contains_match: matchingLineContent.toLowerCase().includes(pattern)
  };
}

// Test case: simulate a chunk from ai-tooling-standard.md
const testChunk = `---
id: ai-tooling-standard
type: standard
title: AI Tooling Standard
status: draft
owner: Technology Operating Partner`;

const chunkStartLine = 0;
const searchPattern = 'standard';

console.log('Testing matching logic...\n');
console.log('Chunk content:');
console.log(testChunk);
console.log('\n' + '='.repeat(60));

console.log(`\nSearching for: "${searchPattern}"`);
console.log('Chunk starts at line:', chunkStartLine);

const result = findMatchingLine(testChunk, searchPattern, chunkStartLine);

console.log('\nRESULT:');
console.log('  Line number:', result.line_number);
console.log('  Line content:', JSON.stringify(result.line_content));
console.log('  Contains match?:', result.contains_match ? '✓ YES' : '✗ NO');

console.log('\n' + '='.repeat(60));
console.log('\nEXPECTED vs BEFORE FIX:');
console.log('  BEFORE (wrong): Line 0: "---" (no match)');
console.log('  AFTER (fixed):  Line 1: "id: ai-tooling-standard" (has match)');
console.log('\nVerdict:', result.line_number === 1 && result.contains_match ? '✓ FIX WORKS!' : '✗ FIX FAILED');
