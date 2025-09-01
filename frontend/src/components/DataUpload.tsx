import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

const DataUpload = () => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const uploadMutation = useMutation({
    mutationFn: api.uploadFile,
    onSuccess: (data) => {
      console.log('Upload successful:', data);
      // Handle successful upload
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
      // For now, we'll just set the file - actual upload will happen on "Process Data"
      // Later we can implement immediate upload if needed
    }
  };

  const handleProcessData = () => {
    if (uploadedFile) {
      uploadMutation.mutate(uploadedFile);
    }
  };

  return (
    <section className="py-24 px-6 bg-muted/30">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-light tracking-tight mb-4">Data Upload</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Upload your screening plate data for analysis. Supports CSV files with BetaGlo, BacTiter, and optical density measurements.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Upload Screening Data
              </CardTitle>
              <CardDescription>
                CSV files with required columns: BG_ldtD, BT_ldtD, OD_WT, OD_tolC, OD_SA
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary/50 transition-colors">
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  {uploadedFile ? (
                    <div className="space-y-2">
                      <CheckCircle className="h-12 w-12 mx-auto text-green-500" />
                      <p className="font-medium">{uploadedFile.name}</p>
                      <p className="text-sm text-muted-foreground">Ready for analysis</p>
                    </div>
                  ) : uploadMutation.isPending ? (
                    <div className="space-y-2">
                      <div className="animate-spin h-12 w-12 mx-auto border-2 border-primary border-t-transparent rounded-full"></div>
                      <p>Processing...</p>
                    </div>
                  ) : uploadMutation.isError ? (
                    <div className="space-y-2">
                      <AlertCircle className="h-12 w-12 mx-auto text-red-500" />
                      <p className="text-red-600">Upload failed</p>
                      <p className="text-sm text-muted-foreground">Please try again</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <FileText className="h-12 w-12 mx-auto text-muted-foreground" />
                      <p>Drop your CSV file here or click to browse</p>
                      <p className="text-sm text-muted-foreground">Maximum file size: 50MB</p>
                    </div>
                  )}
                </label>
              </div>
              
              {uploadedFile && !uploadMutation.isError && (
                <div className="mt-6 space-y-3">
                  <Button 
                    className="w-full"
                    onClick={handleProcessData}
                    disabled={uploadMutation.isPending}
                  >
                    {uploadMutation.isPending ? 'Processing...' : 'Process Data'}
                  </Button>
                  <Button variant="outline" className="w-full">
                    Configure Parameters
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Data Requirements</CardTitle>
              <CardDescription>
                Ensure your data includes these required columns
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="space-y-2">
                  <h4 className="font-medium">Required Columns:</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• BG_ldtD - BetaGlo for ldtD</li>
                    <li>• BT_ldtD - BacTiter for ldtD</li>
                    <li>• OD_WT - Optical density for wild-type strain</li>
                    <li>• OD_tolC - Optical density for ΔtolC strain</li>
                    <li>• OD_SA - Optical density for SA strain</li>
                  </ul>
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-medium">Optional Columns:</h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• Plate identifier</li>
                    <li>• Well position</li>
                    <li>• Treatment ID</li>
                    <li>• Control types</li>
                  </ul>
                </div>

                <div className="pt-4">
                  <Button variant="outline" size="sm">
                    Download Sample Template
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default DataUpload;