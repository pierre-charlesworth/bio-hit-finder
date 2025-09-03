import Header from '@/components/Header';
import Hero from '@/components/Hero';
import Footer from '@/components/Footer';

const Index = () => {
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
        <Hero />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
