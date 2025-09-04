/**
 * WellPositionMapper.tsx
 * 
 * Plate format detection and coordinate mapping utilities
 * Converts well identifiers (A01, B02) to (x,y) coordinates for heatmap rendering
 */

export interface PlateFormat {
  name: string;
  rows: number;
  columns: number;
  totalWells: number;
  wellSpacing: number;
  plateWidth: number;
  plateHeight: number;
}

export interface WellPosition {
  wellId: string;
  row: number;
  column: number;
  x: number;
  y: number;
  rowLabel: string;
  columnLabel: string;
}

export interface PlateLayout {
  format: PlateFormat;
  wells: WellPosition[];
  boundaries: {
    minX: number;
    maxX: number;
    minY: number;
    maxY: number;
  };
}

// Standard plate formats
export const PLATE_FORMATS: Record<string, PlateFormat> = {
  '96': {
    name: '96-well',
    rows: 8,
    columns: 12,
    totalWells: 96,
    wellSpacing: 9.0, // mm
    plateWidth: 127.76, // mm
    plateHeight: 85.48  // mm
  },
  '384': {
    name: '384-well',
    rows: 16,
    columns: 24,
    totalWells: 384,
    wellSpacing: 4.5, // mm
    plateWidth: 127.76, // mm
    plateHeight: 85.48  // mm
  },
  '1536': {
    name: '1536-well',
    rows: 32,
    columns: 48,
    totalWells: 1536,
    wellSpacing: 2.25, // mm
    plateWidth: 127.76, // mm
    plateHeight: 85.48  // mm
  }
};

/**
 * Detects plate format from well identifiers
 */
export function detectPlateFormat(wellIds: string[]): PlateFormat {
  if (wellIds.length === 0) {
    return PLATE_FORMATS['96']; // Default to 96-well
  }

  // Parse all well identifiers to find max row and column
  let maxRow = 0;
  let maxCol = 0;

  for (const wellId of wellIds) {
    const position = parseWellId(wellId);
    if (position) {
      maxRow = Math.max(maxRow, position.row);
      maxCol = Math.max(maxCol, position.column);
    }
  }

  const totalWells = wellIds.length;
  const estimatedWells = (maxRow + 1) * (maxCol + 1);

  // Determine format based on dimensions
  if (maxRow <= 8 && maxCol <= 12) {
    return PLATE_FORMATS['96'];
  } else if (maxRow <= 16 && maxCol <= 24) {
    return PLATE_FORMATS['384'];
  } else if (maxRow <= 32 && maxCol <= 48) {
    return PLATE_FORMATS['1536'];
  }

  // Fallback based on well count
  if (totalWells <= 96) return PLATE_FORMATS['96'];
  if (totalWells <= 384) return PLATE_FORMATS['384'];
  return PLATE_FORMATS['1536'];
}

/**
 * Parses well identifier (A01, B02, etc.) to row/column indices
 */
export function parseWellId(wellId: string): { row: number; column: number; rowLabel: string; columnLabel: string } | null {
  if (!wellId || typeof wellId !== 'string') return null;

  // Handle different well ID formats
  const patterns = [
    /^([A-Z]+)(\d+)$/,  // A01, B12, etc.
    /^([A-Z]+)[-_]?(\d+)$/,  // A-01, B_12, etc.
    /^(\d+)([A-Z]+)$/   // 01A, 12B, etc. (alternative format)
  ];

  for (const pattern of patterns) {
    const match = wellId.toUpperCase().match(pattern);
    if (match) {
      let rowLabel: string, columnLabel: string;
      
      if (pattern === patterns[2]) {
        // Number first format (01A)
        columnLabel = match[1];
        rowLabel = match[2];
      } else {
        // Letter first format (A01)
        rowLabel = match[1];
        columnLabel = match[2];
      }

      const row = rowLabelToIndex(rowLabel);
      const column = parseInt(columnLabel, 10) - 1; // Convert to 0-based

      if (row >= 0 && column >= 0) {
        return {
          row,
          column,
          rowLabel,
          columnLabel
        };
      }
    }
  }

  return null;
}

/**
 * Converts row label (A, B, ..., AA, AB) to 0-based index
 */
function rowLabelToIndex(label: string): number {
  if (!label) return -1;
  
  let index = 0;
  for (let i = 0; i < label.length; i++) {
    const char = label[i];
    const charValue = char.charCodeAt(0) - 'A'.charCodeAt(0) + 1;
    index = index * 26 + charValue;
  }
  return index - 1; // Convert to 0-based
}

/**
 * Converts 0-based row index to row label
 */
function indexToRowLabel(index: number): string {
  let result = '';
  let remaining = index + 1; // Convert to 1-based
  
  while (remaining > 0) {
    remaining--;
    result = String.fromCharCode('A'.charCodeAt(0) + (remaining % 26)) + result;
    remaining = Math.floor(remaining / 26);
  }
  
  return result;
}

/**
 * Calculates well position coordinates for heatmap rendering
 */
export function calculateWellPosition(
  row: number,
  column: number,
  format: PlateFormat,
  containerWidth: number = 800,
  containerHeight: number = 600
): { x: number; y: number } {
  // Calculate relative position within plate (0-1 range)
  const relativeX = format.columns > 1 ? column / (format.columns - 1) : 0.5;
  const relativeY = format.rows > 1 ? row / (format.rows - 1) : 0.5;

  // Add margins for labels and legend
  const margin = 0.1;
  const plotWidth = containerWidth * (1 - 2 * margin);
  const plotHeight = containerHeight * (1 - 2 * margin);

  // Calculate absolute position
  const x = margin * containerWidth + relativeX * plotWidth;
  const y = margin * containerHeight + relativeY * plotHeight;

  return { x, y };
}

/**
 * Creates complete plate layout with all well positions
 */
export function createPlateLayout(
  wellIds: string[],
  containerWidth: number = 800,
  containerHeight: number = 600
): PlateLayout {
  const format = detectPlateFormat(wellIds);
  const wells: WellPosition[] = [];
  
  let minX = Infinity, maxX = -Infinity;
  let minY = Infinity, maxY = -Infinity;

  // Process each well ID
  for (const wellId of wellIds) {
    const parsed = parseWellId(wellId);
    if (!parsed) continue;

    const position = calculateWellPosition(
      parsed.row,
      parsed.column,
      format,
      containerWidth,
      containerHeight
    );

    wells.push({
      wellId,
      row: parsed.row,
      column: parsed.column,
      x: position.x,
      y: position.y,
      rowLabel: parsed.rowLabel,
      columnLabel: parsed.columnLabel
    });

    // Track boundaries
    minX = Math.min(minX, position.x);
    maxX = Math.max(maxX, position.x);
    minY = Math.min(minY, position.y);
    maxY = Math.max(maxY, position.y);
  }

  return {
    format,
    wells,
    boundaries: {
      minX: minX === Infinity ? 0 : minX,
      maxX: maxX === -Infinity ? containerWidth : maxX,
      minY: minY === Infinity ? 0 : minY,
      maxY: maxY === -Infinity ? containerHeight : maxY
    }
  };
}

/**
 * Generates axis labels for plate layout
 */
export function generateAxisLabels(format: PlateFormat): {
  rowLabels: string[];
  columnLabels: string[];
} {
  const rowLabels: string[] = [];
  const columnLabels: string[] = [];

  // Generate row labels (A, B, C, ..., AA, AB, ...)
  for (let i = 0; i < format.rows; i++) {
    rowLabels.push(indexToRowLabel(i));
  }

  // Generate column labels (1, 2, 3, ...)
  for (let i = 1; i <= format.columns; i++) {
    columnLabels.push(i.toString().padStart(2, '0'));
  }

  return { rowLabels, columnLabels };
}

/**
 * Validates well position data
 */
export function validateWellPositions(wells: WellPosition[]): string[] {
  const warnings: string[] = [];

  if (wells.length === 0) {
    warnings.push('No well positions found');
    return warnings;
  }

  // Check for duplicate well IDs
  const uniqueIds = new Set(wells.map(w => w.wellId));
  if (uniqueIds.size !== wells.length) {
    warnings.push(`Duplicate well IDs detected (${wells.length - uniqueIds.size} duplicates)`);
  }

  // Check for invalid coordinates
  const invalidPositions = wells.filter(w => 
    !isFinite(w.x) || !isFinite(w.y) || w.x < 0 || w.y < 0
  );
  if (invalidPositions.length > 0) {
    warnings.push(`${invalidPositions.length} wells have invalid coordinates`);
  }

  // Check for row/column consistency
  const rows = new Set(wells.map(w => w.row));
  const columns = new Set(wells.map(w => w.column));
  const expectedWells = rows.size * columns.size;
  
  if (wells.length < expectedWells * 0.8) {
    warnings.push(`Sparse plate layout detected (${wells.length}/${expectedWells} wells)`);
  }

  return warnings;
}

/**
 * Utility to find nearest well to given coordinates
 */
export function findNearestWell(
  x: number,
  y: number,
  wells: WellPosition[],
  maxDistance: number = 50
): WellPosition | null {
  let nearestWell: WellPosition | null = null;
  let minDistance = maxDistance;

  for (const well of wells) {
    const distance = Math.sqrt(
      Math.pow(x - well.x, 2) + Math.pow(y - well.y, 2)
    );

    if (distance < minDistance) {
      minDistance = distance;
      nearestWell = well;
    }
  }

  return nearestWell;
}