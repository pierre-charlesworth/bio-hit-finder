import Header from '@/components/Header';
import DataUploadBar from '@/components/DataUploadBar';
import Hero from '@/components/Hero';
import AnalysisDashboard from '@/components/AnalysisDashboard';
import WorkGrid from '@/components/WorkGrid';
import About from '@/components/About';
import Contact from '@/components/Contact';
import Footer from '@/components/Footer';

const Index = () => {
  return (
    <div className="min-h-screen">
      <Header />
      <DataUploadBar />
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
