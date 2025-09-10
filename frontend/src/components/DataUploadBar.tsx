import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  ChevronDown,
  Settings,
  Play,
  Database,
  Info,
  FlaskConical,
  Activity,
  Target,
  FileSpreadsheet
} from 'lucide-react';
import { api } from '@/lib/api';
import { useAnalysis } from '@/contexts/AnalysisContext';
import SheetSelector from './SheetSelector';

interface DataUploadBarProps {
  onStatusChange?: (status: 'none' | 'uploaded' | 'sample' | 'processing' | 'error') => void;
  onFileNameChange?: (fileName: string) => void;
  onProcessCallbackChange?: (callback: (() => void) | null) => void;
}

const DataUploadBar = ({ onStatusChange, onFileNameChange, onProcessCallbackChange }: DataUploadBarProps) => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isParametersExpanded, setIsParametersExpanded] = useState(false);
  const [isDataFormatExpanded, setIsDataFormatExpanded] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [useSampleData, setUseSampleData] = useState(false);
  const [showSheetSelector, setShowSheetSelector] = useState(false);
  const [selectedSheet, setSelectedSheet] = useState<string>('');
  
  const { setCurrentAnalysis } = useAnalysis();
  
  // Configuration state
  const [viabilityThreshold, setViabilityThreshold] = useState(0.3);
  const [zScoreCutoff, setZScoreCutoff] = useState(2.0);
  const [useBScoring, setUseBScoring] = useState(true);
  const [edgeEffectThreshold, setEdgeEffectThreshold] = useState(0.1);

  const uploadMutation = useMutation({
    mutationFn: ({ file, sheetName }: { file: File; sheetName?: string }) => api.uploadFile(file, sheetName),
    onSuccess: (data) => {
      console.log('Upload successful:', data);
      setCurrentAnalysis(data);
      onStatusChange?.('uploaded');
      setShowSheetSelector(false);
    },
    onError: (error) => {
      console.error('Upload failed:', error);
      setUploadedFile(null);
      setShowSheetSelector(false);
      onStatusChange?.('error');
    },
  });

  const demoMutation = useMutation({
    mutationFn: () => api.getDemoAnalysis({
      z_threshold: zScoreCutoff,
      vitality_config: {
        tolc_threshold: 0.8,
        wt_threshold: 0.8,
        sa_threshold: 0.8
      },
      viability_column: 'PassViab',
      require_both_stages: true
    }),
    onSuccess: (data) => {
      console.log('Demo analysis successful:', data);
      setCurrentAnalysis(data);
      onStatusChange?.('uploaded');
    },
    onError: (error) => {
      console.error('Demo analysis failed:', error);
      onStatusChange?.('error');
    },
  });

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setSelectedSheet('');
      
      // Check if it's an Excel file
      const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xls');
      
      if (isExcel) {
        // Show sheet selector for Excel files
        setShowSheetSelector(true);
        onStatusChange?.('uploaded');
        onFileNameChange?.(file.name);
      } else {
        // For CSV files, proceed directly
        onStatusChange?.('uploaded');
        onFileNameChange?.(file.name);
        onProcessCallbackChange?.(() => handleProcessData);
      }
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    const file = event.dataTransfer.files?.[0];
    
    if (file && (file.type === 'text/csv' || 
        file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
        file.type === 'application/vnd.ms-excel' ||
        file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
      
      setUploadedFile(file);
      setSelectedSheet('');
      
      // Check if it's an Excel file
      const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xls');
      
      if (isExcel) {
        // Show sheet selector for Excel files
        setShowSheetSelector(true);
        onStatusChange?.('uploaded');
        onFileNameChange?.(file.name);
      } else {
        // For CSV files, proceed directly
        onStatusChange?.('uploaded');
        onFileNameChange?.(file.name);
        onProcessCallbackChange?.(() => handleProcessData);
      }
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
  };

  const handleProcessData = () => {
    onStatusChange?.('processing');
    if (uploadedFile) {
      uploadMutation.mutate({ file: uploadedFile, sheetName: selectedSheet });
    } else if (useSampleData) {
      // Process sample data using demo endpoint
      console.log('Processing sample data...');
      demoMutation.mutate();
    }
  };

  const handleSheetSelected = (sheetName: string) => {
    setSelectedSheet(sheetName);
    setShowSheetSelector(false);
    onProcessCallbackChange?.(() => handleProcessData);
  };

  const handleSheetSelectorClose = () => {
    setShowSheetSelector(false);
    setUploadedFile(null);
    onStatusChange?.('none');
    onFileNameChange?.('');
    onProcessCallbackChange?.(null);
  };

  const handleSampleDataToggle = () => {
    const newUseSampleData = !useSampleData;
    setUseSampleData(newUseSampleData);
    
    if (newUseSampleData) {
      // Clear any uploaded file when using sample data
      setUploadedFile(null);
      onStatusChange?.('sample');
      onFileNameChange?.('');
      onProcessCallbackChange?.(() => handleProcessData);
    } else {
      onStatusChange?.('none');
      onFileNameChange?.('');
      onProcessCallbackChange?.(null);
    }
  };


  return (
    <div className="fixed top-[73px] left-0 right-0 z-40 border-b bg-background/80 backdrop-blur-sm border-border">
      <div className="container-fluid max-w-7xl mx-auto">
        {/* Main Bar - Two Lines */}
        <div className="py-3 space-y-3">
          {/* First Line - Upload Area + Process Button */}
          <div className="flex items-center justify-between">
            {/* Left Side - Upload Area */}
            <div className="flex items-center gap-4">
              <div
                className={`relative h-12 w-12 border-2 border-dashed rounded-lg transition-all duration-200 ${
                  useSampleData
                    ? 'border-muted bg-muted/20 cursor-not-allowed opacity-50'
                    : isDragOver 
                    ? 'border-primary bg-primary/10 cursor-pointer' 
                    : uploadedFile
                    ? 'border-green-500 bg-green-50 dark:bg-green-950 cursor-pointer'
                    : 'border-border hover:border-primary/50 hover:bg-muted/50 cursor-pointer'
                }`}
                onDrop={useSampleData ? undefined : handleDrop}
                onDragOver={useSampleData ? undefined : handleDragOver}
                onDragLeave={useSampleData ? undefined : handleDragLeave}
              >
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload-square"
                  disabled={useSampleData}
                />
                <label 
                  htmlFor="file-upload-square" 
                  className={`absolute inset-0 flex items-center justify-center ${useSampleData ? 'cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  {(uploadMutation.isPending || demoMutation.isPending) ? (
                    <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full"></div>
                  ) : uploadedFile ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : (uploadMutation.isError || demoMutation.isError) ? (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  ) : (
                    <Upload className={`h-5 w-5 ${useSampleData ? 'text-muted-foreground/50' : 'text-muted-foreground'}`} />
                  )}
                </label>
              </div>
              
              {/* Drop Files Text */}
              <div className={`text-sm ${useSampleData ? 'text-muted-foreground/50' : 'text-muted-foreground'}`}>
                <p>{useSampleData ? 'Upload disabled' : 'Drop CSV/Excel or click to upload'}</p>
                <p className="text-xs">{useSampleData ? 'Toggle sample data off' : 'Supports .csv, .xlsx, .xls • Max 50MB'}</p>
              </div>
            </div>

            {/* Right Side - Process Button */}
            <div className="flex items-center">
              <Button 
                size="sm" 
                className="gap-1"
                onClick={handleProcessData}
                disabled={(uploadMutation.isPending || demoMutation.isPending) || (!uploadedFile && !useSampleData)}
              >
                <Play className="h-3 w-3" />
                {(uploadMutation.isPending || demoMutation.isPending) ? 'Processing...' : 'Process'}
              </Button>
            </div>
          </div>

          {/* Second Line - Sample Data Toggle + Parameters + Data Format */}
          <div className="flex items-center justify-between">
            {/* Left Side - Sample Data Toggle */}
            <div className="flex items-center gap-2">
              <Label htmlFor="sample-data-toggle" className="text-sm font-medium">
                Sample Data
              </Label>
              <Switch
                id="sample-data-toggle"
                checked={useSampleData}
                onCheckedChange={handleSampleDataToggle}
              />
            </div>

            {/* Right Side - Action Buttons */}
            <div className="flex items-center gap-2">
              <Button 
                size="sm" 
                variant="outline" 
                className="gap-1"
                onClick={() => setIsParametersExpanded(!isParametersExpanded)}
              >
                <Settings className="h-3 w-3" />
                Parameters
                <ChevronDown className={`h-3 w-3 transition-transform ${isParametersExpanded ? 'rotate-180' : ''}`} />
              </Button>
              <Button 
                size="sm" 
                variant="ghost" 
                className="gap-1 text-muted-foreground hover:text-foreground"
                onClick={() => setIsDataFormatExpanded(!isDataFormatExpanded)}
              >
                <Info className="h-3 w-3" />
                Data Format
                <ChevronDown className={`h-3 w-3 transition-transform ${isDataFormatExpanded ? 'rotate-180' : ''}`} />
              </Button>
            </div>
          </div>
        </div>

        {/* Expandable Data Format Panel */}
        <Collapsible open={isDataFormatExpanded} onOpenChange={setIsDataFormatExpanded}>
          <CollapsibleContent>
            <div className="border-t bg-muted/30 px-6 py-4">
              <div className="mb-4">
                <h3 className="font-medium text-sm mb-3 flex items-center gap-2">
                  <FlaskConical className="h-4 w-4 text-blue-600" />
                  Required CSV Data Format
                </h3>
                <p className="text-xs text-muted-foreground mb-4">
                  Your CSV file must contain the following columns for proper plate analysis. Each measurement type serves a specific biological purpose in the screening assay.
                </p>
              </div>

              <div className="grid lg:grid-cols-2 gap-4">
                {/* Reporter Assay Columns */}
                <Card className="border-blue-200 dark:border-blue-800">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Activity className="h-4 w-4 text-blue-600" />
                      Reporter Assays
                    </CardTitle>
                    <CardDescription className="text-xs">
                      β-galactosidase activity and cell density measurements
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs font-mono">BG_lptA</Badge>
                        <Badge variant="outline" className="text-xs font-mono">BT_lptA</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        <strong><em>lptA</em> reporter:</strong> BetaGlo signal (BG) measures β-galactosidase activity from the <em>lptA</em> promoter. BacTiter signal (BT) normalizes for cell density. The BG/BT ratio indicates <em>lptA</em> expression levels.
                      </p>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs font-mono">BG_ldtD</Badge>
                        <Badge variant="outline" className="text-xs font-mono">BT_ldtD</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        <strong><em>ldtD</em> reporter:</strong> Similar dual-reporter system for <em>ldtD</em> promoter activity. Both reporters help identify compounds affecting envelope stress response pathways.
                      </p>
                    </div>

                    <div className="mt-3 p-2 bg-blue-50 dark:bg-blue-950/30 rounded border border-blue-200 dark:border-blue-800">
                      <p className="text-xs text-blue-800 dark:text-blue-200 font-medium">
                        💡 Ratio Calculation: Reporter_Ratio = BG / BT
                      </p>
                    </div>
                  </CardContent>
                </Card>

                {/* Growth Inhibition Columns */}
                <Card className="border-green-200 dark:border-green-800">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Target className="h-4 w-4 text-green-600" />
                      Growth Measurements
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Optical density readings for bacterial strain viability
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs font-mono">OD_WT</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        <strong>Wild-type strain:</strong> Baseline growth measurement for the parent bacterial strain without genetic modifications.
                      </p>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs font-mono">OD_tolC</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        <strong>tolC knockout:</strong> Strain lacking the TolC efflux pump component, increasing sensitivity to many compounds.
                      </p>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs font-mono">OD_SA</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        <strong>Sensitized strain:</strong> Additional genetic background with enhanced compound sensitivity for hit detection.
                      </p>
                    </div>

                    <div className="mt-3 p-2 bg-green-50 dark:bg-green-950/30 rounded border border-green-200 dark:border-green-800">
                      <p className="text-xs text-green-800 dark:text-green-200 font-medium">
                        🎯 Three-strain screening increases hit detection sensitivity
                      </p>
                    </div>
                  </CardContent>
                </Card>

                {/* Identifier Columns */}
                <Card className="border-orange-200 dark:border-orange-800">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Database className="h-4 w-4 text-orange-600" />
                      Identifiers
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Plate position and compound tracking
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs font-mono">Well_ID</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        <strong>Plate position:</strong> Standard well identifiers (e.g., A01, B12, H24) for 96-, 384-, or 1536-well plates.
                      </p>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs font-mono">Compound_ID</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        <strong>Chemical identifier:</strong> Unique compound codes, catalog numbers, or chemical names for tracking test substances.
                      </p>
                    </div>
                  </CardContent>
                </Card>

                {/* Example Format */}
                <Card className="border-purple-200 dark:border-purple-800">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <FileText className="h-4 w-4 text-purple-600" />
                      Example Format
                    </CardTitle>
                    <CardDescription className="text-xs">
                      Sample CSV structure with proper headers
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-slate-50 dark:bg-slate-900 p-3 rounded border font-mono text-xs overflow-x-auto">
                      <div className="text-purple-600 dark:text-purple-400 mb-2">CSV Header Row:</div>
                      <div className="whitespace-nowrap">
                        Well_ID,Compound_ID,BG_lptA,BT_lptA,BG_ldtD,BT_ldtD,OD_WT,OD_tolC,OD_SA
                      </div>
                      <div className="text-purple-600 dark:text-purple-400 mt-2 mb-1">Sample Data:</div>
                      <div className="whitespace-nowrap text-muted-foreground">
                        A01,DMSO_CTL,1250,850,980,820,0.85,0.82,0.79<br/>
                        A02,CPD_001,890,825,1450,815,0.81,0.45,0.38
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Expandable Parameters Panel */}
        <Collapsible open={isParametersExpanded} onOpenChange={setIsParametersExpanded}>
          <CollapsibleContent>
            <div className="border-t bg-muted/30 px-6 py-4">
              <div className="grid md:grid-cols-3 gap-6">
                {/* Analysis Parameters */}
                <div className="space-y-4">
                  <h3 className="font-medium text-sm">Analysis Parameters</h3>
                  <div className="space-y-3">
                    <div className="space-y-2">
                      <Label htmlFor="viability-threshold" className="text-xs">
                        Viability Threshold ({viabilityThreshold})
                      </Label>
                      <Slider
                        id="viability-threshold"
                        min={0.1}
                        max={0.8}
                        step={0.05}
                        value={[viabilityThreshold]}
                        onValueChange={(value) => setViabilityThreshold(value[0])}
                        className="w-full"
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="zscore-cutoff" className="text-xs">
                        Z-Score Cutoff ({zScoreCutoff})
                      </Label>
                      <Slider
                        id="zscore-cutoff"
                        min={1.0}
                        max={5.0}
                        step={0.1}
                        value={[zScoreCutoff]}
                        onValueChange={(value) => setZScoreCutoff(value[0])}
                        className="w-full"
                      />
                    </div>
                  </div>
                </div>

                {/* Statistical Options */}
                <div className="space-y-4">
                  <h3 className="font-medium text-sm">Statistical Options</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="use-bscoring" className="text-xs">
                        Enable B-Scoring
                      </Label>
                      <Switch
                        id="use-bscoring"
                        checked={useBScoring}
                        onCheckedChange={setUseBScoring}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="edge-effect" className="text-xs">
                        Edge Effect Threshold ({edgeEffectThreshold})
                      </Label>
                      <Slider
                        id="edge-effect"
                        min={0.05}
                        max={0.3}
                        step={0.01}
                        value={[edgeEffectThreshold]}
                        onValueChange={(value) => setEdgeEffectThreshold(value[0])}
                        className="w-full"
                      />
                    </div>
                  </div>
                </div>

                {/* Data Source & Output Options */}
                <div className="space-y-4">
                  <h3 className="font-medium text-sm">Data Source & Options</h3>
                  <div className="space-y-3">
                    {useSampleData ? (
                      <div className="p-3 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800">
                        <div className="flex items-center gap-2 mb-2">
                          <Database className="h-4 w-4 text-blue-600" />
                          <span className="text-sm font-medium text-blue-900 dark:text-blue-100">Sample Dataset</span>
                        </div>
                        <div className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
                          <p>• 384-well screening plate</p>
                          <p>• 2,000 test compounds</p>
                          <p>• Complete BG/BT and OD measurements</p>
                          <p>• Realistic noise and edge effects</p>
                        </div>
                      </div>
                    ) : (
                      <Button variant="outline" size="sm" className="w-full justify-start gap-2">
                        <FileText className="h-3 w-3" />
                        Download Template
                      </Button>
                    )}
                    
                    <div className="text-xs text-muted-foreground space-y-1">
                      <p className="font-medium">Required columns:</p>
                      <p>BG_ldtD, BT_ldtD, OD_WT, OD_tolC, OD_SA</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </div>

      {/* Sheet Selector Dialog */}
      <Dialog open={showSheetSelector} onOpenChange={setShowSheetSelector}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileSpreadsheet className="h-5 w-5" />
              Excel Sheet Selection
            </DialogTitle>
          </DialogHeader>
          {uploadedFile && (
            <SheetSelector
              file={uploadedFile}
              onSheetSelected={handleSheetSelected}
              onClose={handleSheetSelectorClose}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DataUploadBar;