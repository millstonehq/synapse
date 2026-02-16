import { extractWikilinks, validateWikilinkExists } from '../../src/lib/graph';

describe('Graph utilities', () => {
  describe('extractWikilinks', () => {
    it('should extract simple wikilinks', () => {
      const content = 'This is a [[Test Link]] in the document.';
      const links = extractWikilinks(content);
      expect(links).toEqual(['Test Link']);
    });
    
    it('should extract multiple wikilinks', () => {
      const content = 'References: [[Policy A]], [[Standard B]], and [[Process C]].';
      const links = extractWikilinks(content);
      expect(links).toEqual(['Policy A', 'Standard B', 'Process C']);
    });
    
    it('should extract wikilinks with display text', () => {
      const content = 'See [[Long Document Title|Short Name]] for details.';
      const links = extractWikilinks(content);
      expect(links).toEqual(['Long Document Title']);
    });
    
    it('should not include duplicates', () => {
      const content = '[[Same Link]] appears twice: [[Same Link]].';
      const links = extractWikilinks(content);
      expect(links).toEqual(['Same Link']);
    });
    
    it('should handle empty content', () => {
      const links = extractWikilinks('');
      expect(links).toEqual([]);
    });
    
    it('should handle content without wikilinks', () => {
      const content = 'This is plain text without any links.';
      const links = extractWikilinks(content);
      expect(links).toEqual([]);
    });
    
    it('should handle malformed wikilinks', () => {
      const content = 'This [[incomplete and ] not valid ]] link.';
      const links = extractWikilinks(content);
      expect(links).toEqual([]);
    });
  });
  
  describe('validateWikilinkExists', () => {
    const existingFiles = new Set([
      '10_Policies/security-policy.md',
      '20_Standards/change-control-standard.md',
      '30_Processes/change-management.md',
      '60_Systems/payments-api.md',
      'security-policy.md',
      'change-control-standard',
      'payments-api'
    ]);
    
    it('should validate existing file with full path', () => {
      const exists = validateWikilinkExists('change-management', existingFiles);
      expect(exists).toBe(true);
    });
    
    it('should validate existing file with just name', () => {
      const exists = validateWikilinkExists('security-policy', existingFiles);
      expect(exists).toBe(true);
    });
    
    it('should validate file without extension', () => {
      const exists = validateWikilinkExists('change-control-standard', existingFiles);
      expect(exists).toBe(true);
    });
    
    it('should return false for non-existent file', () => {
      const exists = validateWikilinkExists('non-existent-doc', existingFiles);
      expect(exists).toBe(false);
    });
    
    it('should handle empty link target', () => {
      const exists = validateWikilinkExists('', existingFiles);
      expect(exists).toBe(false);
    });
  });
});