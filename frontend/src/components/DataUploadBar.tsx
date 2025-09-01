import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbSeparator } from '@/components/ui/breadcrumb';
import { Badge } from '@/components/ui/badge';
import { 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  ChevronDown,
  Settings,
  Download,
  Play
} from 'lucide-react';
import { api } from '@/lib/api';

const DataUploadBar = () => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

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
        <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
          {/* Collapsed Bar */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-4">
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem>
                    <BreadcrumbLink className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Data
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  {uploadedFile && (
                    <>
                      <BreadcrumbSeparator />
                      <BreadcrumbItem>
                        <BreadcrumbLink className="max-w-32 truncate">
                          {uploadedFile.name}
                        </BreadcrumbLink>
                      </BreadcrumbItem>
                    </>
                  )}
                </BreadcrumbList>
              </Breadcrumb>
              {getStatusBadge()}
            </div>

            <div className="flex items-center gap-2">
              {uploadedFile && (
                <>
                  <Button size="sm" variant="outline" className="gap-1">
                    <Settings className="h-3 w-3" />
                    Configure
                  </Button>
                  <Button 
                    size="sm" 
                    className="gap-1"
                    onClick={handleProcessData}
                    disabled={uploadMutation.isPending}
                  >
                    <Play className="h-3 w-3" />
                    {uploadMutation.isPending ? 'Processing...' : 'Process'}
                  </Button>
                </>
              )}
              
              <CollapsibleTrigger asChild>
                <Button size="sm" variant="ghost" className="gap-1">
                  <ChevronDown className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                  {isExpanded ? 'Collapse' : 'Upload'}
                </Button>
              </CollapsibleTrigger>
            </div>
          </div>

          {/* Expanded Content */}
          <CollapsibleContent>
            <div className="pb-6">
              <div className="grid md:grid-cols-2 gap-6">
                {/* Upload Section */}
                <div className="space-y-4">
                  <h3 className="font-medium flex items-center gap-2">
                    <Upload className="h-4 w-4" />
                    Upload Screening Data
                  </h3>
                  <div className="border-2 border-dashed border-border rounded-lg p-6 text-center hover:border-primary/50 transition-colors">
                    <input
                      type="file"
                      accept=".csv"
                      onChange={handleFileUpload}
                      className="hidden"
                      id="file-upload-bar"
                    />
                    <label htmlFor="file-upload-bar" className="cursor-pointer">
                      {uploadedFile ? (
                        <div className="space-y-2">
                          <CheckCircle className="h-8 w-8 mx-auto text-green-500" />
                          <p className="font-medium">{uploadedFile.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <FileText className="h-8 w-8 mx-auto text-muted-foreground" />
                          <p className="text-sm">Drop CSV or click to browse</p>
                          <p className="text-xs text-muted-foreground">Max 50MB</p>
                        </div>
                      )}
                    </label>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="space-y-4">
                  <h3 className="font-medium">Quick Actions</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <Button variant="outline" size="sm" className="justify-start gap-2">
                      <Download className="h-4 w-4" />
                      Sample Template
                    </Button>
                    <Button variant="outline" size="sm" className="justify-start gap-2">
                      <Settings className="h-4 w-4" />
                      Parameters
                    </Button>
                  </div>
                  
                  <div className="text-xs text-muted-foreground space-y-1">
                    <p className="font-medium">Required columns:</p>
                    <p>BG_ldtD, BT_ldtD, OD_WT, OD_tolC, OD_SA</p>
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