import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  ChevronDown,
  Settings,
  Play,
  Database
} from 'lucide-react';
import { api } from '@/lib/api';

interface DataUploadBarProps {
  onStatusChange?: (status: 'none' | 'uploaded' | 'sample' | 'processing' | 'error') => void;
  onFileNameChange?: (fileName: string) => void;
}

const DataUploadBar = ({ onStatusChange, onFileNameChange }: DataUploadBarProps) => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isParametersExpanded, setIsParametersExpanded] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [useSampleData, setUseSampleData] = useState(false);
  
  // Configuration state
  const [viabilityThreshold, setViabilityThreshold] = useState(0.3);
  const [zScoreCutoff, setZScoreCutoff] = useState(2.0);
  const [useBScoring, setUseBScoring] = useState(true);
  const [edgeEffectThreshold, setEdgeEffectThreshold] = useState(0.1);

  const uploadMutation = useMutation({
    mutationFn: api.uploadFile,
    onSuccess: (data) => {
      console.log('Upload successful:', data);
      onStatusChange?.('uploaded');
    },
    onError: (error) => {
      console.error('Upload failed:', error);
      setUploadedFile(null);
      onStatusChange?.('error');
    },
  });

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      onStatusChange?.('uploaded');
      onFileNameChange?.(file.name);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    const file = event.dataTransfer.files?.[0];
    if (file && file.type === 'text/csv') {
      setUploadedFile(file);
      onStatusChange?.('uploaded');
      onFileNameChange?.(file.name);
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
      uploadMutation.mutate(uploadedFile);
    } else if (useSampleData) {
      // Process sample data
      console.log('Processing sample data...');
      uploadMutation.mutate(new File(['sample,data'], 'sample-data.csv', { type: 'text/csv' }));
    }
  };

  const handleSampleDataToggle = () => {
    const newUseSampleData = !useSampleData;
    setUseSampleData(newUseSampleData);
    
    if (newUseSampleData) {
      // Clear any uploaded file when using sample data
      setUploadedFile(null);
      onStatusChange?.('sample');
      onFileNameChange?.('');
    } else {
      onStatusChange?.('none');
      onFileNameChange?.('');
    }
  };


  return (
    <div className="fixed top-[73px] left-0 right-0 z-40 border-b bg-background/80 backdrop-blur-sm border-border">
      <div className="container-fluid max-w-7xl mx-auto">
        {/* Main Bar */}
        <div className="flex items-center justify-between py-3">
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
                accept=".csv"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload-square"
                disabled={useSampleData}
              />
              <label 
                htmlFor="file-upload-square" 
                className={`absolute inset-0 flex items-center justify-center ${useSampleData ? 'cursor-not-allowed' : 'cursor-pointer'}`}
              >
                {uploadMutation.isPending ? (
                  <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full"></div>
                ) : uploadedFile ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : uploadMutation.isError ? (
                  <AlertCircle className="h-5 w-5 text-red-500" />
                ) : (
                  <Upload className={`h-5 w-5 ${useSampleData ? 'text-muted-foreground/50' : 'text-muted-foreground'}`} />
                )}
              </label>
            </div>
            
            {/* Drop CSV Text */}
            <div className={`text-sm ${useSampleData ? 'text-muted-foreground/50' : 'text-muted-foreground'}`}>
              <p>{useSampleData ? 'Upload disabled' : 'Drop CSV or click to upload'}</p>
              <p className="text-xs">{useSampleData ? 'Toggle sample data off' : 'Max 50MB'}</p>
            </div>
          </div>

          {/* Center - Sample Data Toggle */}
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
            {(uploadedFile || useSampleData) && (
              <Button 
                size="sm" 
                className="gap-1"
                onClick={handleProcessData}
                disabled={uploadMutation.isPending}
              >
                <Play className="h-3 w-3" />
                {uploadMutation.isPending ? 'Processing...' : 'Process'}
              </Button>
            )}
            
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
          </div>
        </div>

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
    </div>
  );
};

export default DataUploadBar;