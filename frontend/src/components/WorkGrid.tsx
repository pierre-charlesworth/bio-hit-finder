import { Card } from '@/components/ui/card';

const WorkGrid = () => {
  const features = [
    {
      id: 1,
      title: 'B-Score Analysis',
      category: 'Statistical Methods',
      description: 'Advanced B-scoring with iterative normalization for accurate hit identification'
    },
    {
      id: 2,
      title: 'Edge Effect Detection',
      category: 'Quality Control',
      description: 'Automated spatial analysis and correction for plate-based screening'
    },
    {
      id: 3,
      title: 'Multi-Strain Support',
      category: 'Flexibility',
      description: 'Simultaneous analysis of wild-type, ΔtolC, and SA strain data'
    },
    {
      id: 4,
      title: 'Export & Reporting',
      category: 'Data Management',
      description: 'Comprehensive CSV, PDF, and ZIP export capabilities'
    }
  ];

  return (
    <section id="work" className="py-24 bg-muted/30">
      <div className="container-fluid max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-fluid-xl font-light tracking-tight mb-4">
            Platform Features
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Comprehensive tools for high-throughput screening analysis with 
            advanced statistical methods and quality control.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
          {features.map((feature, index) => (
            <Card 
              key={feature.id} 
              className="group overflow-hidden border-0 shadow-none hover-lift bg-transparent"
            >
              <div className="aspect-[4/3] overflow-hidden bg-muted flex items-center justify-center">
                <div className="text-8xl font-light text-muted-foreground opacity-20">
                  {String(feature.id).padStart(2, '0')}
                </div>
              </div>
              
              <div className="p-6">
                <div className="text-sm text-muted-foreground mb-2">
                  {feature.category}
                </div>
                
                <h3 className="text-xl font-medium mb-3 group-hover:text-muted-foreground transition-colors">
                  {feature.title}
                </h3>
                
                <p className="text-muted-foreground text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default WorkGrid;