import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, FileSpreadsheet, SheetIcon } from 'lucide-react';
import { api } from '@/lib/api';

interface SheetSelectorProps {
  file: File;
  onSheetSelected?: (sheetName: string) => void;
  onClose?: () => void;
}

interface SheetInfo {
  filename: string;
  file_size: number;
  sheet_names: string[];
  total_sheets: number;
  success: boolean;
}

const SheetSelector = ({ file, onSheetSelected, onClose }: SheetSelectorProps) => {
  const [sheets, setSheets] = useState<SheetInfo | null>(null);
  const [selectedSheet, setSelectedSheet] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSheets = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const sheetData = await api.getExcelSheets(file);
        setSheets(sheetData);
        
        // Auto-select first sheet if only one sheet exists
        if (sheetData.sheet_names.length === 1) {
          setSelectedSheet(sheetData.sheet_names[0]);
          onSheetSelected?.(sheetData.sheet_names[0]);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to read Excel sheets');
        console.error('Failed to fetch Excel sheets:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSheets();
  }, [file]);

  const handleSheetSelection = () => {
    if (selectedSheet && onSheetSelected) {
      onSheetSelected(selectedSheet);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isLoading) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5" />
            Reading Excel File
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2 text-sm text-muted-foreground">Analyzing sheets...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-red-600">Error Reading File</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">{error}</p>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!sheets) {
    return null;
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileSpreadsheet className="h-5 w-5" />
          Select Excel Sheet
        </CardTitle>
        <CardDescription>
          {sheets.filename} • {formatFileSize(sheets.file_size)}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Available sheets:</span>
          <Badge variant="secondary">
            {sheets.total_sheets} sheet{sheets.total_sheets !== 1 ? 's' : ''}
          </Badge>
        </div>

        {sheets.total_sheets === 1 ? (
          <div className="bg-muted/50 p-3 rounded-lg">
            <div className="flex items-center gap-2">
              <SheetIcon className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">{sheets.sheet_names[0]}</span>
              <Badge variant="default" size="sm">Auto-selected</Badge>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <Select value={selectedSheet} onValueChange={setSelectedSheet}>
              <SelectTrigger>
                <SelectValue placeholder="Choose a sheet to process..." />
              </SelectTrigger>
              <SelectContent>
                {sheets.sheet_names.map((sheetName) => (
                  <SelectItem key={sheetName} value={sheetName}>
                    <div className="flex items-center gap-2">
                      <SheetIcon className="h-4 w-4" />
                      {sheetName}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <div className="flex gap-2 pt-2">
          <Button variant="outline" onClick={onClose} className="flex-1">
            Cancel
          </Button>
          <Button 
            onClick={handleSheetSelection} 
            className="flex-1"
            disabled={!selectedSheet && sheets.total_sheets > 1}
          >
            Continue
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default SheetSelector;