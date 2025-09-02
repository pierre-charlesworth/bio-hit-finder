# Development Notes

This document tracks ongoing issues, refinements needed, and future improvements for the bio-hit-finder frontend.

## Current Issues & Refinements Needed

### Cell Envelope Diagram Interactive Areas
**Status**: Needs refinement  
**Date**: 2025-09-02  
**Issue**: The coordinate-based interactive areas for the CellEnvelopeDiagram component need further refinement for more precise component selection.

**Current State**: 
- Using percentage-based coordinates over a JPEG image
- 8 interactive components (LPS, Porin, Outer Membrane, Lipoproteins, Periplasmic Space, Peptidoglycan, Inner Membrane, Cytoplasm)
- Basic coordinate mapping implemented but needs fine-tuning

**Improvements Needed**:
- Test actual click/hover behavior with users to identify imprecise areas
- Consider creating custom SVG overlay paths for pixel-perfect selection
- Potentially implement different coordinate sets for different screen sizes/aspect ratios
- Add visual feedback improvements (better highlighting, smoother transitions)

**Alternative Solutions Explored**:
- Vector conversion: SVG provided was actually JPEG wrapped in SVG, not true vector paths
- Manual SVG path creation could provide cleaner selection but requires significant time investment

**Files Affected**:
- `/src/components/CellEnvelopeDiagram.tsx` (lines 29-102: cellComponents array)
- `/public/cell-envelope-diagram.jpeg`

---

## Future Improvements

### General
- [ ] Performance optimization for large datasets
- [ ] Accessibility improvements across all components  
- [ ] Mobile responsiveness testing and refinements

### Scientific Content
- [ ] Add more scientific tooltips and explanations
- [ ] Expand educational content based on user feedback
- [ ] Consider adding animations for biological processes

---

## Completed Items

### Cell Envelope Diagram Implementation  
**Date**: 2025-09-02  
**Completed**: Basic interactive diagram with image-based coordinate mapping, hover effects, guided tour feature, and scientific tooltips integration.