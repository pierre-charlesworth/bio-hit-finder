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
  Play
} from 'lucide-react';
import { api } from '@/lib/api';

const DataUploadBar = () => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isParametersExpanded, setIsParametersExpanded] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  
  // Configuration state
  const [viabilityThreshold, setViabilityThreshold] = useState(0.3);
  const [zScoreCutoff, setZScoreCutoff] = useState(2.0);
  const [useBScoring, setUseBScoring] = useState(true);
  const [edgeEffectThreshold, setEdgeEffectThreshold] = useState(0.1);

  const uploadMutation = useMutation({
    mutationFn: api.uploadFile,
    onSuccess: (data) => {
      console.log('Upload successful:', data);
    },
    onError: (error) => {
      console.error('Upload failed:', error);
      setUploadedFile(null);
    },
  });

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragOver(false);
    const file = event.dataTransfer.files?.[0];
    if (file && file.type === 'text/csv') {
      setUploadedFile(file);
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
    if (uploadedFile) {
      uploadMutation.mutate(uploadedFile);
    }
  };

  const getStatusBadge = () => {
    if (uploadMutation.isError) {
      return <Badge variant="destructive" className="gap-1"><AlertCircle className="h-3 w-3" />Failed</Badge>;
    }
    if (uploadMutation.isPending) {
      return <Badge variant="secondary" className="gap-1">Processing...</Badge>;
    }
    if (uploadedFile) {
      return <Badge variant="secondary" className="gap-1"><CheckCircle className="h-3 w-3" />Ready</Badge>;
    }
    return <Badge variant="outline" className="gap-1"><Upload className="h-3 w-3" />No Data</Badge>;
  };

  return (
    <div className="fixed top-[73px] left-0 right-0 z-40 border-b bg-background/80 backdrop-blur-sm border-border">
      <div className="container-fluid max-w-7xl mx-auto">
        {/* Main Bar */}
        <div className="flex items-center justify-between py-3">
          {/* Left Side - Square Upload/Drop Area */}
          <div className="flex items-center gap-4">
            <div
              className={`relative h-12 w-12 border-2 border-dashed rounded-lg cursor-pointer transition-all duration-200 ${
                isDragOver 
                  ? 'border-primary bg-primary/10' 
                  : uploadedFile
                  ? 'border-green-500 bg-green-50 dark:bg-green-950'
                  : 'border-border hover:border-primary/50 hover:bg-muted/50'
              }`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <input
                type="file"
                accept=".csv"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload-square"
              />
              <label htmlFor="file-upload-square" className="absolute inset-0 flex items-center justify-center cursor-pointer">
                {uploadMutation.isPending ? (
                  <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full"></div>
                ) : uploadedFile ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : uploadMutation.isError ? (
                  <AlertCircle className="h-5 w-5 text-red-500" />
                ) : (
                  <Upload className="h-5 w-5 text-muted-foreground" />
                )}
              </label>
            </div>
            
            {/* File Info */}
            <div className="flex items-center gap-3">
              {uploadedFile ? (
                <div className="flex items-center gap-2">
                  <div className="text-sm">
                    <p className="font-medium truncate max-w-40">{uploadedFile.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  {getStatusBadge()}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">
                  <p>Drop CSV file or click to upload</p>
                  <p className="text-xs">Max 50MB</p>
                </div>
              )}
            </div>
          </div>

          {/* Right Side - Action Buttons */}
          <div className="flex items-center gap-2">
            {uploadedFile && (
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

                {/* Output Options */}
                <div className="space-y-4">
                  <h3 className="font-medium text-sm">Output Options</h3>
                  <div className="space-y-3">
                    <Button variant="outline" size="sm" className="w-full justify-start gap-2">
                      <FileText className="h-3 w-3" />
                      Download Template
                    </Button>
                    
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