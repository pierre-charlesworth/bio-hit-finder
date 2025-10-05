import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Download, Search, Filter, ChevronUp, ChevronDown } from 'lucide-react';
import { AnalysisResult } from '@/types/analysis';

interface DataTableProps {
  analysisData: AnalysisResult;
  className?: string;
}

type SortDirection = 'asc' | 'desc' | null;

const DataTable = ({ analysisData, className = '' }: DataTableProps) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(new Set([
    'Well', 'PlateID', 'Z_lptA', 'Z_ldtD', 'Stage1_ReporterHit',
    'Stage2_VitalityHit', 'Stage3_PlatformHit', 'PassViab'
  ]));

  // Define all available columns with metadata
  const columnDefinitions = useMemo(() => [
    { key: 'Well', label: 'Well', category: 'Basic' },
    { key: 'PlateID', label: 'Plate ID', category: 'Basic' },
    { key: 'Row', label: 'Row', category: 'Basic' },
    { key: 'Column', label: 'Column', category: 'Basic' },

    // Reporter data
    { key: 'Ratio_lptA', label: 'Ratio lptA', category: 'Reporter' },
    { key: 'Ratio_ldtD', label: 'Ratio ldtD', category: 'Reporter' },
    { key: 'Z_lptA', label: 'Z lptA', category: 'Reporter' },
    { key: 'Z_ldtD', label: 'Z ldtD', category: 'Reporter' },
    { key: 'B_lptA', label: 'B lptA', category: 'Reporter' },
    { key: 'B_ldtD', label: 'B ldtD', category: 'Reporter' },

    // Vitality data
    { key: 'OD_WT', label: 'OD WT', category: 'Vitality' },
    { key: 'OD_tolC', label: 'OD tolC', category: 'Vitality' },
    { key: 'OD_SA', label: 'OD SA', category: 'Vitality' },
    { key: 'WT%', label: 'WT%', category: 'Vitality' },
    { key: 'tolC%', label: 'tolC%', category: 'Vitality' },
    { key: 'SA%', label: 'SA%', category: 'Vitality' },

    // Hit calling
    { key: 'Stage1_ReporterHit', label: 'Reporter Hit', category: 'Hits' },
    { key: 'Stage2_VitalityHit', label: 'Vitality Hit', category: 'Hits' },
    { key: 'Stage3_PlatformHit', label: 'Platform Hit', category: 'Hits' },
    { key: 'Stage3_HitType', label: 'Hit Type', category: 'Hits' },
    { key: 'Stage3_Confidence', label: 'Confidence', category: 'Hits' },

    // QC
    { key: 'PassViab', label: 'Pass Viability', category: 'QC' },
    { key: 'Stage1_ViabilityWarning', label: 'Viability Warning', category: 'QC' },
  ], []);

  // Get unique categories
  const categories = useMemo(() =>
    [...new Set(columnDefinitions.map(col => col.category))],
    [columnDefinitions]
  );

  // Filter and sort data
  const processedData = useMemo(() => {
    let filtered = [...analysisData.results];

    // Apply search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(row =>
        Object.entries(row).some(([key, value]) =>
          String(value).toLowerCase().includes(search)
        )
      );
    }

    // Apply sorting
    if (sortColumn && sortDirection) {
      filtered.sort((a: any, b: any) => {
        const aVal = a[sortColumn];
        const bVal = b[sortColumn];

        if (aVal === bVal) return 0;
        if (aVal == null) return 1;
        if (bVal == null) return -1;

        const comparison = aVal < bVal ? -1 : 1;
        return sortDirection === 'asc' ? comparison : -comparison;
      });
    }

    return filtered;
  }, [analysisData.results, searchTerm, sortColumn, sortDirection]);

  // Handle column sort
  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(prev =>
        prev === 'asc' ? 'desc' : prev === 'desc' ? null : 'asc'
      );
      if (sortDirection === 'desc') {
        setSortColumn(null);
      }
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  // Toggle column visibility
  const toggleColumn = (column: string) => {
    setVisibleColumns(prev => {
      const next = new Set(prev);
      if (next.has(column)) {
        next.delete(column);
      } else {
        next.add(column);
      }
      return next;
    });
  };

  // Format cell value
  const formatCell = (key: string, value: any) => {
    if (value == null || value === '') return '—';

    if (typeof value === 'boolean') {
      return (
        <Badge variant={value ? 'default' : 'outline'} className="text-xs">
          {value ? 'Yes' : 'No'}
        </Badge>
      );
    }

    if (typeof value === 'number') {
      if (key.includes('Confidence')) {
        return (value * 100).toFixed(1) + '%';
      }
      if (key.includes('%')) {
        return (value * 100).toFixed(1) + '%';
      }
      if (key.includes('Z_') || key.includes('B_')) {
        return value.toFixed(2);
      }
      if (key.includes('Ratio')) {
        return value.toFixed(3);
      }
      if (key.includes('OD')) {
        return value.toFixed(4);
      }
      return value.toFixed(2);
    }

    return String(value);
  };

  // Export to CSV
  const exportCSV = () => {
    const headers = columnDefinitions
      .filter(col => visibleColumns.has(col.key))
      .map(col => col.label);

    const rows = processedData.map(row =>
      columnDefinitions
        .filter(col => visibleColumns.has(col.key))
        .map(col => {
          const value = (row as any)[col.key];
          return value != null ? String(value) : '';
        })
    );

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis_data_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const visibleColumnDefs = columnDefinitions.filter(col => visibleColumns.has(col.key));

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Analysis Data Table</CardTitle>
            <CardDescription>
              Showing {processedData.length} of {analysisData.results.length} wells
            </CardDescription>
          </div>
          <Button onClick={exportCSV} variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {/* Controls */}
        <div className="flex gap-4 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search all columns..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select
            value={visibleColumns.size.toString()}
            onValueChange={(value) => {
              if (value === 'all') {
                setVisibleColumns(new Set(columnDefinitions.map(c => c.key)));
              } else if (value === 'basic') {
                setVisibleColumns(new Set(['Well', 'PlateID', 'Z_lptA', 'Z_ldtD', 'Stage3_PlatformHit']));
              }
            }}
          >
            <SelectTrigger className="w-48">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Column preset" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="basic">Basic Columns</SelectItem>
              <SelectItem value="all">All Columns</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Column toggles by category */}
        <div className="mb-4 space-y-2">
          {categories.map(category => (
            <div key={category} className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium text-muted-foreground min-w-20">
                {category}:
              </span>
              {columnDefinitions
                .filter(col => col.category === category)
                .map(col => (
                  <Button
                    key={col.key}
                    variant={visibleColumns.has(col.key) ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => toggleColumn(col.key)}
                    className="text-xs h-7"
                  >
                    {col.label}
                  </Button>
                ))}
            </div>
          ))}
        </div>

        {/* Table */}
        <div className="border rounded-lg overflow-auto max-h-[600px]">
          <Table>
            <TableHeader className="sticky top-0 bg-background z-10">
              <TableRow>
                {visibleColumnDefs.map(col => (
                  <TableHead
                    key={col.key}
                    className="cursor-pointer select-none hover:bg-muted/50"
                    onClick={() => handleSort(col.key)}
                  >
                    <div className="flex items-center gap-1">
                      <span>{col.label}</span>
                      {sortColumn === col.key && (
                        sortDirection === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
                      )}
                    </div>
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {processedData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={visibleColumnDefs.length} className="text-center text-muted-foreground">
                    No data found
                  </TableCell>
                </TableRow>
              ) : (
                processedData.map((row: any, index) => (
                  <TableRow key={index}>
                    {visibleColumnDefs.map(col => (
                      <TableCell key={col.key} className="font-mono text-sm">
                        {formatCell(col.key, row[col.key])}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};

export default DataTable;
