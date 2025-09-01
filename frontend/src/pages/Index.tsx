import Header from '@/components/Header';
import Hero from '@/components/Hero';
import DataUpload from '@/components/DataUpload';
import AnalysisDashboard from '@/components/AnalysisDashboard';
import WorkGrid from '@/components/WorkGrid';
import About from '@/components/About';
import Contact from '@/components/Contact';
import Footer from '@/components/Footer';

const Index = () => {
  return (
    <div className="min-h-screen">
      <Header />
      <main>
        <Hero />
        <DataUpload />
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
