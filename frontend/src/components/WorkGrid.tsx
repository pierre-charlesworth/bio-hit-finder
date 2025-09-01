import { Card } from '@/components/ui/card';

const WorkGrid = () => {
  const methodologyAreas = [
    {
      id: 1,
      title: 'Biological Rationale',
      category: '🔬 Reporter Systems',
      description: 'Dual-reporter system using lptA (LPS transport) and ldtD (peptidoglycan) for envelope stress detection. Three-strain vitality screening with E. coli WT, ΔtolC, and S. aureus controls provides OM-selective compound identification.',
      details: [
        'σE-regulated lptA reporter for LPS transport disruption',
        'Cpx-regulated ldtD reporter for peptidoglycan stress',
        'Three-strain selectivity profiling for therapeutic windows'
      ]
    },
    {
      id: 2,
      title: 'Statistical Methods',
      category: '📊 Robust Analysis',
      description: 'Robust Z-scores using median/MAD resist outliers and systematic errors. B-scoring corrects row/column bias through median-polish algorithm. ATP-based viability gating ensures metabolically active cell analysis.',
      details: [
        'Z = (value - median) / (1.4826 × MAD)',
        'B-scoring for spatial artifact correction',
        'BG/BT ratios normalize expression variability'
      ]
    },
    {
      id: 3,
      title: 'Assay Design',
      category: '⚡ HTS Platform',
      description: '384-well plates with synchronized protocols manage environmental factors. OD measurements reveal growth inhibition patterns. BetaGlo/BacTiter chemistry provides ATP-normalized reporter activity.',
      details: [
        'Expected OM permeabilizers: WT>80%, ΔtolC≤80%, SA>80%',
        'Environmental control for temperature, humidity, evaporation',
        'Time-course measurements with synchronized protocols'
      ]
    },
    {
      id: 4,
      title: 'Quality Control',
      category: '🧮 Data Integrity',
      description: 'Multi-dimensional QC with Z\' factor assessment, edge effect detection, and spatial correlation analysis. Automated flagging of systematic biases ensures reliable hit identification with ~1% platform hit rate.',
      details: [
        'Z\' factor ≥0.5 excellent, ≥0.3 acceptable performance',
        'Moran\'s I spatial correlation quantification',
        'Expected hit rates: 8% reporter, 6.5% vitality, 1% platform'
      ]
    }
  ];

  return (
    <section id="work" className="py-24 bg-muted/30">
      <div className="container-fluid max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-fluid-xl font-light tracking-tight mb-4">
            Scientific Methodology
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Advanced biotech screening platform combining robust statistical analysis, 
            biological reporter systems, and comprehensive quality control for antimicrobial discovery.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
          {methodologyAreas.map((area, index) => (
            <Card 
              key={area.id} 
              className="group overflow-hidden border-0 shadow-none hover-lift bg-transparent"
            >
              <div className="aspect-[4/3] overflow-hidden bg-muted flex items-center justify-center">
                <div className="text-8xl font-light text-muted-foreground opacity-20">
                  {String(area.id).padStart(2, '0')}
                </div>
              </div>
              
              <div className="p-6">
                <div className="text-sm text-muted-foreground mb-2">
                  {area.category}
                </div>
                
                <h3 className="text-xl font-medium mb-3 group-hover:text-muted-foreground transition-colors">
                  {area.title}
                </h3>
                
                <p className="text-muted-foreground text-sm leading-relaxed mb-4">
                  {area.description}
                </p>
                
                <div className="space-y-2">
                  {area.details.map((detail, detailIndex) => (
                    <div key={detailIndex} className="flex items-start gap-2">
                      <div className="w-1 h-1 rounded-full bg-primary mt-2 flex-shrink-0"></div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {detail}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default WorkGrid;