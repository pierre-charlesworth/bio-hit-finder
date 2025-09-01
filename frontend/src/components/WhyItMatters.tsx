import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Target, Shield, TrendingUp } from 'lucide-react';
import ScientificTooltip from '@/components/ui/scientific-tooltip';

const WhyItMatters = () => {
  const crisisStats = [
    {
      icon: AlertTriangle,
      value: "700,000+",
      label: "Deaths annually from AMR infections",
      trend: "Rising 5% per year"
    },
    {
      icon: Shield,
      value: ">90%",
      label: "Potential antibiotics blocked by outer membrane",
      trend: "Major barrier to discovery"
    },
    {
      icon: Target,
      value: "1987",
      label: "Last new antibiotic class discovered",
      trend: "37+ year gap"
    },
    {
      icon: TrendingUp,
      value: "$100B+",
      label: "Annual economic impact of AMR",
      trend: "Growing healthcare burden"
    }
  ];

  const permeabilizerAdvantages = [
    {
      title: "Synergistic Approach",
      description: "Combines existing antibiotics with membrane permeabilizers for enhanced efficacy",
      benefit: "Revives ineffective drugs"
    },
    {
      title: "Reduced Resistance",
      description: "Targeting membrane integrity creates multiple simultaneous stress points",
      benefit: "Harder to develop resistance"
    },
    {
      title: "Selective Toxicity",
      description: "Gram-negative specific targeting leaves human cells unaffected",
      benefit: "Improved safety profile"
    },
    {
      title: "Rapid Development",
      description: "Adjuvant approach faster than discovering entirely new antibiotic classes",
      benefit: "Shorter path to clinic"
    }
  ];

  return (
    <section className="py-16 bg-primary/5 border-y">
      <div className="container-fluid max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-light tracking-tight mb-4">
            Why Outer Membrane Permeabilizers Matter
          </h2>
          <p className="text-muted-foreground max-w-3xl mx-auto">
            Addressing the antimicrobial resistance crisis requires innovative approaches beyond traditional antibiotic discovery. 
            The <ScientificTooltip term="LPS">outer membrane barrier</ScientificTooltip> represents both the challenge and the opportunity.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-12 mb-16">
          {/* AMR Crisis Section */}
          <div>
            <div className="flex items-center gap-3 mb-6">
              <AlertTriangle className="h-6 w-6 text-destructive" />
              <h3 className="text-2xl font-light">The AMR Crisis</h3>
            </div>
            
            <div className="space-y-6">
              <p className="text-muted-foreground leading-relaxed">
                Gram-negative bacteria pose an unprecedented threat to global health. Their distinctive 
                <ScientificTooltip term="LPS"> outer membrane</ScientificTooltip> creates a formidable barrier 
                that renders most antibiotics ineffective, while rapid resistance development outpaces drug discovery.
              </p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {crisisStats.map((stat, index) => {
                  const IconComponent = stat.icon;
                  return (
                    <Card key={index} className="border-l-4 border-l-destructive">
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <IconComponent className="h-5 w-5 text-destructive mt-0.5" />
                          <div className="flex-1">
                            <div className="text-2xl font-light text-foreground mb-1">
                              {stat.value}
                            </div>
                            <div className="text-sm text-muted-foreground mb-2">
                              {stat.label}
                            </div>
                            <Badge variant="outline" className="text-xs">
                              {stat.trend}
                            </Badge>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>

              <div className="bg-background/50 p-4 rounded-lg border-l-4 border-l-orange-500">
                <div className="font-medium mb-2">Key Challenge:</div>
                <p className="text-sm text-muted-foreground">
                  The <ScientificTooltip term="LPS">lipopolysaccharide</ScientificTooltip> molecules in the outer membrane 
                  create both physical and electrostatic barriers. This <strong>impermeability crisis</strong> means that 
                  compounds with proven bacterial targets often cannot reach those targets in living cells.
                </p>
              </div>
            </div>
          </div>

          {/* Permeabilizer Solution Section */}
          <div>
            <div className="flex items-center gap-3 mb-6">
              <Target className="h-6 w-6 text-primary" />
              <h3 className="text-2xl font-light">The Permeabilizer Solution</h3>
            </div>
            
            <div className="space-y-6">
              <p className="text-muted-foreground leading-relaxed">
                Rather than discovering entirely new antibiotics, <strong>outer membrane permeabilizers</strong> work as 
                adjuvants, sensitizing Gram-negative bacteria to existing drugs. This combination therapy approach 
                offers a faster path to clinical impact.
              </p>

              <div className="space-y-4">
                {permeabilizerAdvantages.map((advantage, index) => (
                  <Card key={index} className="border-l-4 border-l-primary">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <h4 className="font-medium text-foreground mb-2">
                            {advantage.title}
                          </h4>
                          <p className="text-sm text-muted-foreground mb-3">
                            {advantage.description}
                          </p>
                          <Badge variant="secondary" className="text-xs">
                            {advantage.benefit}
                          </Badge>
                        </div>
                        <div className="text-2xl font-light text-primary opacity-60">
                          {String(index + 1).padStart(2, '0')}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="bg-primary/10 p-4 rounded-lg border-l-4 border-l-primary">
                <div className="font-medium mb-2">Therapeutic Strategy:</div>
                <p className="text-sm text-muted-foreground">
                  <strong>Permeabilizer + Traditional Antibiotic</strong> combinations can restore 
                  efficacy to drugs that have become ineffective against resistant strains. The 
                  <ScientificTooltip term="ΔtolC">tolC deletion strain</ScientificTooltip> serves as a 
                  proof-of-concept, demonstrating how compromised efflux increases antibiotic sensitivity.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom CTA Section */}
        <div className="text-center bg-background/50 p-8 rounded-lg border">
          <h3 className="text-xl font-medium mb-4">
            Identifying the Next Generation of Antimicrobial Adjuvants
          </h3>
          <p className="text-muted-foreground mb-6 max-w-2xl mx-auto">
            The BREAKthrough platform uses <ScientificTooltip term="lptA">envelope stress reporters</ScientificTooltip> and 
            <ScientificTooltip term="B-scoring">robust statistical methods</ScientificTooltip> to systematically identify 
            compounds that can overcome the outer membrane barrier while maintaining selectivity.
          </p>
          <div className="flex justify-center gap-2">
            <Badge variant="outline">Dual-Reporter System</Badge>
            <Badge variant="outline">Three-Strain Profiling</Badge>
            <Badge variant="outline">Quality Control</Badge>
            <Badge variant="outline">Statistical Rigor</Badge>
          </div>
        </div>
      </div>
    </section>
  );
};

export default WhyItMatters;