import Header from '@/components/Header';
import WhyItMatters from '@/components/WhyItMatters';
import ScreeningWorkflow from '@/components/ScreeningWorkflow';
import QCLearningModule from '@/components/QCLearningModule';
import PlatformValidation from '@/components/PlatformValidation';
import ExpertCommentary from '@/components/ExpertCommentary';
import Footer from '@/components/Footer';

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
      <main>
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