import { useState } from 'react';
import Header from '@/components/Header';
import DataUploadBar from '@/components/DataUploadBar';
import Hero from '@/components/Hero';
import AnalysisDashboard from '@/components/AnalysisDashboard';
import WorkGrid from '@/components/WorkGrid';
import About from '@/components/About';
import Contact from '@/components/Contact';
import Footer from '@/components/Footer';

const Index = () => {
  const [dataStatus, setDataStatus] = useState<'none' | 'uploaded' | 'sample' | 'processing' | 'error'>('none');
  const [fileName, setFileName] = useState<string>('');

  return (
    <div className="min-h-screen">
      <Header dataStatus={dataStatus} fileName={fileName} />
      <DataUploadBar 
        onStatusChange={setDataStatus}
        onFileNameChange={setFileName}
      />
      <main>
        <Hero />
        <AnalysisDashboard />
        <WorkGrid />
        <About />
        <Contact />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
