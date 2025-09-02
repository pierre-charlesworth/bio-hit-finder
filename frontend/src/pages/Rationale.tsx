import Header from '@/components/Header';
import WhyItMatters from '@/components/WhyItMatters';
import ScreeningWorkflow from '@/components/ScreeningWorkflow';
import QCLearningModule from '@/components/QCLearningModule';
import PlatformValidation from '@/components/PlatformValidation';
import ExpertCommentary from '@/components/ExpertCommentary';
import Footer from '@/components/Footer';
import CellEnvelopeDiagram from '@/components/CellEnvelopeDiagram';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Microscope } from 'lucide-react';

const Rationale = () => {
  return (
    <div className="min-h-screen">
      <Header 
        dataStatus="none" 
        fileName=""
        backendStatus="connected"
        canProcess={false}
        isProcessing={false}
      />
      <main className="pt-24">
        <div className="container-fluid max-w-7xl mx-auto py-8">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-light tracking-tight mb-4">
              Scientific Rationale
            </h1>
            <p className="text-muted-foreground max-w-3xl mx-auto">
              Understanding the scientific methodology behind outer membrane permeabilizer discovery,
              dual-reporter systems, and robust statistical approaches for high-throughput screening.
            </p>
          </div>
        </div>
        <WhyItMatters />
        
        {/* Interactive Cell Envelope Diagram */}
        <section className="py-16">
          <div className="container-fluid max-w-7xl mx-auto">
            <Card className="max-w-5xl mx-auto">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl font-light tracking-tight flex items-center justify-center gap-3">
                  <Microscope className="h-6 w-6 text-primary" />
                  Interactive Cell Envelope Architecture
                </CardTitle>
                <p className="text-muted-foreground mt-2">
                  Explore the Gram-negative bacterial cell envelope structure and understand 
                  how outer membrane permeabilizers interact with key cellular components.
                </p>
              </CardHeader>
              <CardContent className="pt-6">
                <CellEnvelopeDiagram />
              </CardContent>
            </Card>
          </div>
        </section>
        
        <ScreeningWorkflow />
        <QCLearningModule />
        <PlatformValidation />
        <ExpertCommentary />
      </main>
      <Footer />
    </div>
  );
};

export default Rationale;