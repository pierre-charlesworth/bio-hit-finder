/**
 * PlateSelector.tsx
 * 
 * Family/extract filtering system for multi-plate analysis
 * Handles plate grouping, family-based filtering, and data aggregation
 */

import { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { 
  Search, 
  Filter, 
  Layers, 
  CheckSquare, 
  Square,
  RotateCcw,
  Info
} from 'lucide-react';
import { AnalysisResult } from '@/types/analysis';
import { DataProcessor, WellData } from '../shared/DataProcessor';

export interface PlateGroup {
  id: string;
  name: string;
  plateIds: string[];
  family?: string;
  extract?: string;
  wellCount: number;
  hitCount: number;
  averageViability: number;
}

export interface FilterCriteria {
  selectedPlates: string[];
  selectedFamilies: string[];
  selectedExtracts: string[];
  minViability: number;
  minHitRate: number;
  searchQuery: string;
}

export interface PlateSelectorProps {
  analysisData: AnalysisResult;
  onSelectionChange: (plateIds: string[]) => void;
  selectedPlates: string[];
  onFilterChange?: (filteredData: WellData[]) => void;
  showGrouping?: boolean;
  showStatistics?: boolean;
  className?: string;
}

/**
 * Multi-plate selection and filtering interface
 */
const PlateSelector = ({
  analysisData,
  onSelectionChange,
  selectedPlates,
  onFilterChange,
  showGrouping = true,
  showStatistics = true,
  className = ''
}: PlateSelectorProps) => {

  const [filterCriteria, setFilterCriteria] = useState<FilterCriteria>({
    selectedPlates: selectedPlates,
    selectedFamilies: [],
    selectedExtracts: [],
    minViability: 0,
    minHitRate: 0,
    searchQuery: ''
  });

  const [groupingMode, setGroupingMode] = useState<'plate' | 'family' | 'extract'>('plate');

  // Process analysis data to extract plate information
  const { plateGroups, families, extracts, allPlates } = useMemo(() => {
    const wellData = DataProcessor.extractWellData(analysisData);
    
    // Group wells by plate
    const plateMap = new Map<string, WellData[]>();
    wellData.forEach(well => {
      const plateId = well.PlateID || 'Unknown';
      if (!plateMap.has(plateId)) {
        plateMap.set(plateId, []);
      }
      plateMap.get(plateId)!.push(well);
    });

    // Create plate groups with statistics
    const groups: PlateGroup[] = [];
    const familySet = new Set<string>();
    const extractSet = new Set<string>();

    plateMap.forEach((wells, plateId) => {
      // Extract family/extract info from plate ID or well data
      const { family, extract } = extractFamilyInfo(plateId, wells);
      
      if (family) familySet.add(family);
      if (extract) extractSet.add(extract);

      // Calculate statistics
      const viableWells = wells.filter(w => w.PassViab);
      const hitWells = wells.filter(w => 
        Math.abs(w.Z_lptA || 0) >= 2 || Math.abs(w.Z_ldtD || 0) >= 2
      );

      groups.push({
        id: plateId,
        name: plateId,
        plateIds: [plateId],
        family,
        extract,
        wellCount: wells.length,
        hitCount: hitWells.length,
        averageViability: viableWells.length / wells.length
      });
    });

    return {
      plateGroups: groups,
      families: Array.from(familySet).sort(),
      extracts: Array.from(extractSet).sort(),
      allPlates: groups.map(g => g.id).sort()
    };
  }, [analysisData]);

  // Filter plates based on criteria
  const filteredPlates = useMemo(() => {
    return plateGroups.filter(plate => {
      // Family filter
      if (filterCriteria.selectedFamilies.length > 0 && 
          !filterCriteria.selectedFamilies.includes(plate.family || '')) {
        return false;
      }

      // Extract filter  
      if (filterCriteria.selectedExtracts.length > 0 && 
          !filterCriteria.selectedExtracts.includes(plate.extract || '')) {
        return false;
      }

      // Viability filter
      if (plate.averageViability < filterCriteria.minViability) {
        return false;
      }

      // Hit rate filter
      const hitRate = plate.wellCount > 0 ? plate.hitCount / plate.wellCount : 0;
      if (hitRate < filterCriteria.minHitRate) {
        return false;
      }

      // Search query
      if (filterCriteria.searchQuery) {
        const query = filterCriteria.searchQuery.toLowerCase();
        const searchableText = [
          plate.name,
          plate.family || '',
          plate.extract || ''
        ].join(' ').toLowerCase();
        
        if (!searchableText.includes(query)) {
          return false;
        }
      }

      return true;
    });
  }, [plateGroups, filterCriteria]);

  // Group plates by the selected grouping mode
  const groupedPlates = useMemo(() => {
    if (groupingMode === 'plate') {
      return [{ name: 'All Plates', plates: filteredPlates }];
    }

    const groups = new Map<string, PlateGroup[]>();
    
    filteredPlates.forEach(plate => {
      const groupKey = groupingMode === 'family' 
        ? (plate.family || 'Unknown Family')
        : (plate.extract || 'Unknown Extract');
      
      if (!groups.has(groupKey)) {
        groups.set(groupKey, []);
      }
      groups.get(groupKey)!.push(plate);
    });

    return Array.from(groups.entries()).map(([name, plates]) => ({
      name,
      plates
    })).sort((a, b) => a.name.localeCompare(b.name));
  }, [filteredPlates, groupingMode]);

  // Handle plate selection
  const handlePlateSelection = (plateId: string, selected: boolean) => {
    const newSelection = selected
      ? [...selectedPlates, plateId]
      : selectedPlates.filter(id => id !== plateId);
    
    onSelectionChange(newSelection);
    
    setFilterCriteria(prev => ({
      ...prev,
      selectedPlates: newSelection
    }));
  };

  // Handle bulk selection
  const handleSelectAll = () => {
    const allPlateIds = filteredPlates.map(p => p.id);
    onSelectionChange(allPlateIds);
    setFilterCriteria(prev => ({
      ...prev,
      selectedPlates: allPlateIds
    }));
  };

  const handleSelectNone = () => {
    onSelectionChange([]);
    setFilterCriteria(prev => ({
      ...prev,
      selectedPlates: []
    }));
  };

  // Calculate summary statistics
  const summaryStats = useMemo(() => {
    const selectedPlateData = plateGroups.filter(p => selectedPlates.includes(p.id));
    const totalWells = selectedPlateData.reduce((sum, p) => sum + p.wellCount, 0);
    const totalHits = selectedPlateData.reduce((sum, p) => sum + p.hitCount, 0);
    const avgViability = selectedPlateData.length > 0
      ? selectedPlateData.reduce((sum, p) => sum + p.averageViability, 0) / selectedPlateData.length
      : 0;

    return {
      plateCount: selectedPlates.length,
      wellCount: totalWells,
      hitCount: totalHits,
      hitRate: totalWells > 0 ? totalHits / totalWells : 0,
      averageViability: avgViability
    };
  }, [plateGroups, selectedPlates]);

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Layers className="h-5 w-5" />
          Plate Selection
          <Badge variant="secondary" className="ml-auto">
            {selectedPlates.length} / {allPlates.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        
        {/* Search and Filters */}
        <div className="space-y-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search plates, families, or extracts..."
              value={filterCriteria.searchQuery}
              onChange={(e) => setFilterCriteria(prev => ({
                ...prev,
                searchQuery: e.target.value
              }))}
              className="pl-10"
            />
          </div>

          {/* Grouping Mode */}
          {showGrouping && (
            <div className="flex items-center gap-2">
              <Label className="text-sm">Group by:</Label>
              <Select value={groupingMode} onValueChange={(v) => setGroupingMode(v as any)}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="plate">Plate</SelectItem>
                  <SelectItem value="family">Family</SelectItem>
                  <SelectItem value="extract">Extract</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Family Filter */}
          {families.length > 0 && (
            <div>
              <Label className="text-sm mb-2 block">Families</Label>
              <div className="flex flex-wrap gap-2">
                {families.map(family => (
                  <div key={family} className="flex items-center space-x-2">
                    <Checkbox
                      id={`family-${family}`}
                      checked={filterCriteria.selectedFamilies.includes(family)}
                      onCheckedChange={(checked) => {
                        setFilterCriteria(prev => ({
                          ...prev,
                          selectedFamilies: checked
                            ? [...prev.selectedFamilies, family]
                            : prev.selectedFamilies.filter(f => f !== family)
                        }));
                      }}
                    />
                    <Label htmlFor={`family-${family}`} className="text-sm">
                      {family}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Bulk Selection */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSelectAll}
            className="flex items-center gap-1"
          >
            <CheckSquare className="h-4 w-4" />
            All
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleSelectNone}
            className="flex items-center gap-1"
          >
            <Square className="h-4 w-4" />
            None
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setFilterCriteria({
              selectedPlates: [],
              selectedFamilies: [],
              selectedExtracts: [],
              minViability: 0,
              minHitRate: 0,
              searchQuery: ''
            })}
            className="flex items-center gap-1 ml-auto"
          >
            <RotateCcw className="h-4 w-4" />
            Reset
          </Button>
        </div>

        {/* Plate Groups */}
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {groupedPlates.map(group => (
            <div key={group.name} className="space-y-2">
              {group.name !== 'All Plates' && (
                <h4 className="text-sm font-medium text-muted-foreground border-b pb-1">
                  {group.name}
                </h4>
              )}
              
              <div className="grid gap-2">
                {group.plates.map(plate => (
                  <div
                    key={plate.id}
                    className={`flex items-center justify-between p-2 rounded border ${
                      selectedPlates.includes(plate.id) 
                        ? 'bg-primary/10 border-primary/20' 
                        : 'bg-muted/20'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <Checkbox
                        checked={selectedPlates.includes(plate.id)}
                        onCheckedChange={(checked) => 
                          handlePlateSelection(plate.id, checked as boolean)
                        }
                      />
                      <div>
                        <div className="font-medium text-sm">{plate.name}</div>
                        {showStatistics && (
                          <div className="text-xs text-muted-foreground">
                            {plate.wellCount} wells • {plate.hitCount} hits • 
                            {(plate.averageViability * 100).toFixed(1)}% viable
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex gap-1">
                      <Badge variant="outline" className="text-xs">
                        {((plate.hitCount / plate.wellCount) * 100).toFixed(1)}%
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Summary Statistics */}
        {showStatistics && selectedPlates.length > 0 && (
          <div className="border-t pt-3">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-muted-foreground">Total Wells</div>
                <div className="font-medium">{summaryStats.wellCount.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Total Hits</div>
                <div className="font-medium">{summaryStats.hitCount.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Hit Rate</div>
                <div className="font-medium">{(summaryStats.hitRate * 100).toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-muted-foreground">Avg Viability</div>
                <div className="font-medium">{(summaryStats.averageViability * 100).toFixed(1)}%</div>
              </div>
            </div>
          </div>
        )}

        {/* Info Message */}
        {filteredPlates.length === 0 && (
          <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="flex items-start gap-2">
              <Info className="h-4 w-4 text-yellow-600 mt-0.5" />
              <div className="text-sm text-yellow-800">
                No plates match the current filter criteria. Try adjusting your search or filters.
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * Extracts family and extract information from plate ID or well data
 */
function extractFamilyInfo(plateId: string, wells: WellData[]): { family?: string; extract?: string } {
  // Try to extract from plate ID patterns
  // Common patterns: FAMILY_EXTRACT_001, FAM-EXT-01, etc.
  const patterns = [
    /^([A-Z]+)_([A-Z0-9]+)_\d+$/,  // FAMILY_EXTRACT_001
    /^([A-Z]+)-([A-Z0-9]+)-\d+$/,  // FAMILY-EXTRACT-01
    /^([A-Z]+)(\d+)$/               // FAMILY001
  ];

  for (const pattern of patterns) {
    const match = plateId.match(pattern);
    if (match) {
      return {
        family: match[1],
        extract: match[2] || undefined
      };
    }
  }

  // Fallback: try to detect from well count or naming patterns
  if (wells.length <= 96) {
    return { family: 'Small Scale' };
  } else if (wells.length <= 384) {
    return { family: 'Medium Scale' };  
  } else {
    return { family: 'High Throughput' };
  }
}

export default PlateSelector;