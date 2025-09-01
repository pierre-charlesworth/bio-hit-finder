import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ArrowRight, Circle, ChevronDown, Microscope } from 'lucide-react';
import { useState } from 'react';
import { useApiTest, useDemoAnalysis } from '@/hooks/useApi';
import { useToast } from '@/hooks/use-toast';
import { useAnalysis } from '@/contexts/AnalysisContext';

const Hero = () => {
  const { data: apiTest, isLoading, isError } = useApiTest();
  const { toast } = useToast();
  const demoMutation = useDemoAnalysis();
  const { setCurrentAnalysis, setIsAnalyzing, setAnalysisError } = useAnalysis();
  const [isScientificBackgroundOpen, setIsScientificBackgroundOpen] = useState(false);

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
            Advanced biotech screening platform for drug discovery research,
            featuring B-scoring analysis and automated hit identification.
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

          {/* Scientific Background Expander */}
          <div className="mt-12 max-w-4xl mx-auto text-reveal" style={{animationDelay: '0.4s'}}>
            <Collapsible open={isScientificBackgroundOpen} onOpenChange={setIsScientificBackgroundOpen}>
              <CollapsibleTrigger asChild>
                <Button 
                  variant="ghost" 
                  className="w-full group hover:bg-muted/50 p-4 h-auto justify-between"
                >
                  <div className="flex items-center gap-3">
                    <Microscope className="h-5 w-5 text-primary" />
                    <span className="font-medium">Scientific Background & Methodology</span>
                  </div>
                  <ChevronDown className={`h-4 w-4 transition-transform duration-200 ${isScientificBackgroundOpen ? 'rotate-180' : ''}`} />
                </Button>
              </CollapsibleTrigger>
              
              <CollapsibleContent>
                <div className="mt-6 p-6 bg-muted/30 rounded-lg border text-left space-y-6 text-sm">
                  {/* B-Scoring Analysis */}
                  <div>
                    <h3 className="text-base font-semibold mb-3 text-primary">B-Score Statistical Analysis</h3>
                    <p className="mb-3 text-muted-foreground">
                      The B-score method addresses systematic biases in high-throughput screening by applying a two-way median polish 
                      to remove row and column effects from screening plates. This approach is particularly effective for identifying 
                      compounds with genuine biological activity while minimizing false positives due to spatial artifacts.
                    </p>
                    <div className="bg-background/50 p-4 rounded border-l-4 border-l-primary">
                      <p className="font-medium mb-2">Mathematical Foundation:</p>
                      <p className="text-xs font-mono mb-2">B-score = (raw_value - row_median - column_median + plate_median) / MAD</p>
                      <p className="text-xs text-muted-foreground">
                        Where MAD (Median Absolute Deviation) provides robust scaling: MAD = 1.4826 × median(|x - median(x)|)
                      </p>
                    </div>
                  </div>

                  {/* Outer Membrane Disruption */}
                  <div>
                    <h3 className="text-base font-semibold mb-3 text-primary">Outer Membrane Disruption Detection</h3>
                    <p className="mb-3 text-muted-foreground">
                      Our platform specializes in identifying compounds that compromise bacterial outer membrane integrity. 
                      We employ a dual-reporter system measuring both membrane permeability and cell viability to distinguish 
                      between specific outer membrane effects and general cytotoxicity.
                    </p>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="bg-background/50 p-4 rounded">
                        <p className="font-medium mb-2">Reporter Strains:</p>
                        <ul className="text-xs space-y-1 text-muted-foreground">
                          <li>• <strong>lptA:</strong> LPS transport deficiency</li>
                          <li>• <strong>ldtD:</strong> Peptidoglycan crosslinking</li>
                          <li>• <strong>ΔtolC:</strong> Efflux pump deficiency</li>
                          <li>• <strong>Wild-type:</strong> Reference control</li>
                        </ul>
                      </div>
                      <div className="bg-background/50 p-4 rounded">
                        <p className="font-medium mb-2">Detection Methods:</p>
                        <ul className="text-xs space-y-1 text-muted-foreground">
                          <li>• <strong>BetaGlo:</strong> ATP-based viability</li>
                          <li>• <strong>BacTiter:</strong> Metabolic activity</li>
                          <li>• <strong>OD600:</strong> Cell density</li>
                          <li>• <strong>Ratio Analysis:</strong> BG/BT ratios</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  {/* Quality Control */}
                  <div>
                    <h3 className="text-base font-semibold mb-3 text-primary">Quality Control & Edge Effects</h3>
                    <p className="mb-3 text-muted-foreground">
                      Automated detection of common screening artifacts including edge effects, pipetting errors, and systematic 
                      biases. The system implements multiple QC metrics to ensure data reliability and reproducibility.
                    </p>
                    <div className="bg-background/50 p-4 rounded border-l-4 border-l-orange-500">
                      <p className="font-medium mb-2">QC Parameters:</p>
                      <ul className="text-xs space-y-1 text-muted-foreground">
                        <li>• <strong>Z' Factor:</strong> Assay quality assessment (≥0.5 excellent)</li>
                        <li>• <strong>CV Analysis:</strong> Coefficient of variation for controls</li>
                        <li>• <strong>Spatial Analysis:</strong> Heat map visualization of plate effects</li>
                        <li>• <strong>Control Wells:</strong> DMSO, positive controls, blanks</li>
                        <li>• <strong>Edge Detection:</strong> Automated flagging of perimeter effects</li>
                      </ul>
                    </div>
                  </div>

                  {/* Statistical Robustness */}
                  <div>
                    <h3 className="text-base font-semibold mb-3 text-primary">Statistical Robustness</h3>
                    <p className="mb-3 text-muted-foreground">
                      Implementation of robust statistical methods that are resistant to outliers and capable of handling 
                      non-normal data distributions commonly found in biological screening data.
                    </p>
                    <div className="grid md:grid-cols-3 gap-4 text-xs">
                      <div className="bg-background/50 p-3 rounded">
                        <p className="font-medium mb-2">Robust Statistics:</p>
                        <ul className="space-y-1 text-muted-foreground">
                          <li>• Median-based scaling</li>
                          <li>• MAD normalization</li>
                          <li>• Outlier detection</li>
                        </ul>
                      </div>
                      <div className="bg-background/50 p-3 rounded">
                        <p className="font-medium mb-2">Normalization:</p>
                        <ul className="space-y-1 text-muted-foreground">
                          <li>• Plate-wise correction</li>
                          <li>• Position effects</li>
                          <li>• Batch normalization</li>
                        </ul>
                      </div>
                      <div className="bg-background/50 p-3 rounded">
                        <p className="font-medium mb-2">Hit Identification:</p>
                        <ul className="space-y-1 text-muted-foreground">
                          <li>• Configurable Z-score cutoffs</li>
                          <li>• Multiple testing correction</li>
                          <li>• Dose-response validation</li>
                        </ul>
                      </div>
                    </div>
                  </div>
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