import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ArrowRight, ChevronDown, Microscope } from 'lucide-react';
import { useState } from 'react';
import CellEnvelopeDiagram from './CellEnvelopeDiagram';
import { useApiTest, useDemoAnalysis } from '@/hooks/useApi';
import { useToast } from '@/hooks/use-toast';
import { useAnalysis } from '@/contexts/AnalysisContext';

const Hero = () => {
  const { data: apiTest, isLoading, isError } = useApiTest();
  const { toast } = useToast();
  const demoMutation = useDemoAnalysis();
  const { setCurrentAnalysis, setIsAnalyzing, setAnalysisError } = useAnalysis();
  const [isCellDiagramOpen, setIsCellDiagramOpen] = useState(false);

  const handleDemoClick = () => {
    // Start analysis state
    setIsAnalyzing(true);
    setAnalysisError(null);
    
    demoMutation.mutate({}, {
      onSuccess: (data) => {
        console.log('Demo analysis completed:', data);
        
        // Store analysis results in context
        setCurrentAnalysis(data);
        setIsAnalyzing(false);
        
        toast({
          title: "Demo Analysis Complete",
          description: `Found ${data.summary?.stage3_platform_hits || 0} platform hits out of ${data.total_wells} wells`,
        });
      },
      onError: (error) => {
        console.error('Demo analysis failed:', error);
        
        // Update error state
        setIsAnalyzing(false);
        setAnalysisError(error.message || 'Demo analysis failed');
        
        toast({
          title: "Demo Analysis Failed",
          description: "There was an error running the demo analysis",
          variant: "destructive",
        });
      }
    });
  };

  return (
    <section className="min-h-screen flex items-center justify-center pt-8">
      <div className="container-fluid max-w-7xl mx-auto text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-fluid-3xl font-light tracking-tight text-reveal">
            BREAKthrough OM{' '}
            <span className="font-medium">Screening Platform</span>
          </h1>
          
          <p className="text-lg md:text-xl text-muted-foreground mt-8 max-w-2xl mx-auto text-reveal" style={{animationDelay: '0.2s'}}>
            Dual-reporter screening platform for identifying outer membrane permeabilizers 
            and envelope-disrupting compounds using robust statistical analysis and quality control.
          </p>

          {/* Platform Features */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-16 max-w-4xl mx-auto text-reveal" style={{animationDelay: '0.3s'}}>
            <div className="text-center p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors">
              <div className="text-2xl font-light mb-2">01</div>
              <div className="text-sm font-medium mb-1">B-Score Analysis</div>
              <div className="text-xs text-muted-foreground">Statistical Methods</div>
            </div>
            <div className="text-center p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors">
              <div className="text-2xl font-light mb-2">02</div>
              <div className="text-sm font-medium mb-1">Edge Detection</div>
              <div className="text-xs text-muted-foreground">Quality Control</div>
            </div>
            <div className="text-center p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors">
              <div className="text-2xl font-light mb-2">03</div>
              <div className="text-sm font-medium mb-1">Multi-Strain</div>
              <div className="text-xs text-muted-foreground">Flexibility</div>
            </div>
            <div className="text-center p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors">
              <div className="text-2xl font-light mb-2">04</div>
              <div className="text-sm font-medium mb-1">Export & Reports</div>
              <div className="text-xs text-muted-foreground">Data Management</div>
            </div>
          </div>

          {/* Cell Envelope Diagram */}
          <div className="mt-12 max-w-4xl mx-auto text-reveal" style={{animationDelay: '0.4s'}}>
            <Collapsible open={isCellDiagramOpen} onOpenChange={setIsCellDiagramOpen}>
              <CollapsibleTrigger asChild>
                <Button 
                  variant="ghost" 
                  className="w-full group hover:bg-muted/50 p-4 h-auto justify-between"
                >
                  <div className="flex items-center gap-3">
                    <Microscope className="h-5 w-5 text-primary" />
                    <span className="font-medium">Interactive Cell Envelope Diagram</span>
                  </div>
                  <ChevronDown className={`h-4 w-4 transition-transform duration-200 ${isCellDiagramOpen ? 'rotate-180' : ''}`} />
                </Button>
              </CollapsibleTrigger>
              
              <CollapsibleContent>
                <div className="mt-6">
                  <CellEnvelopeDiagram />
                </div>
              </CollapsibleContent>
            </Collapsible>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center mt-12 text-reveal" style={{animationDelay: '0.5s'}}>
            <Button 
              size="lg" 
              className="group"
            >
              Upload Data
              <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Button>
            
            <Button 
              variant="outline" 
              size="lg"
              className="hover-lift"
              onClick={handleDemoClick}
              disabled={demoMutation.isPending}
            >
              {demoMutation.isPending ? 'Loading Demo...' : 'View Demo'}
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;