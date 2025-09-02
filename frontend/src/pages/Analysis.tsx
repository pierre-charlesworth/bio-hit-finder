import { useState } from 'react';
import Header from '@/components/Header';
import DataUploadBar from '@/components/DataUploadBar';
import AnalysisDashboard from '@/components/AnalysisDashboard';
import WorkGrid from '@/components/WorkGrid';
import Footer from '@/components/Footer';

const Analysis = () => {
  const [dataStatus, setDataStatus] = useState<'none' | 'uploaded' | 'sample' | 'processing' | 'error'>('none');
  const [fileName, setFileName] = useState<string>('');
  const [processCallback, setProcessCallback] = useState<(() => void) | null>(null);

  const canProcess = dataStatus === 'uploaded' || dataStatus === 'sample';
  const isProcessing = dataStatus === 'processing';

  return (
    <div className="min-h-screen">
      <Header 
        dataStatus={dataStatus} 
        fileName={fileName}
        backendStatus="connected"
        onProcessData={processCallback || undefined}
        canProcess={canProcess}
        isProcessing={isProcessing}
      />
      <DataUploadBar 
        onStatusChange={setDataStatus}
        onFileNameChange={setFileName}
        onProcessCallbackChange={setProcessCallback}
      />
      <main className="pt-32">
        <div className="container-fluid max-w-7xl mx-auto py-8">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-light tracking-tight mb-4">
              Analysis Dashboard
            </h1>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Upload your plate data to get comprehensive statistical analysis, quality control metrics, 
              and hit identification using robust B-scoring methodology.
            </p>
          </div>
        </div>
        <AnalysisDashboard />
        <WorkGrid />
      </main>
      <Footer />
    </div>
  );
};

export default Analysis;