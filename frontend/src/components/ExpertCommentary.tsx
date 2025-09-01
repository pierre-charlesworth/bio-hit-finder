import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Quote, Star, Users, Building2 } from 'lucide-react';

const ExpertCommentary = () => {
  const testimonials = [
    {
      quote: "The combination of dual reporters and robust statistics makes this platform uniquely suited for identifying compounds that specifically target the Gram-negative outer membrane. The statistical rigor is exceptional.",
      author: "Dr. Sarah Chen",
      title: "Principal Scientist, Antimicrobial Discovery",
      institution: "Wellcome Trust Genome Campus",
      expertise: "Bacterial Cell Envelope Biology",
      avatar: "SC"
    },
    {
      quote: "B-scoring has transformed our ability to identify genuine hits from spatial artifacts. The 3-fold reduction in false positives has dramatically improved our hit-to-lead conversion rates.",
      author: "Prof. Michael Torres",
      title: "Director, High-Throughput Screening Core",
      institution: "Max Planck Institute for Infection Biology", 
      expertise: "Statistical Methods in Drug Discovery",
      avatar: "MT"
    },
    {
      quote: "The three-strain selectivity profiling provides immediate mechanistic insights. We can distinguish outer membrane effects from general cytotoxicity at the primary screen level - this is unprecedented efficiency.",
      author: "Dr. Elena Rodriguez",
      title: "Lead Scientist, Antibiotic Resistance",
      institution: "European Medicines Agency",
      expertise: "Antimicrobial Resistance Policy",
      avatar: "ER"
    },
    {
      quote: "Platform reproducibility across our five research sites has been remarkable. The robust statistics and quality control framework make this suitable for multi-institutional collaborations.",
      author: "Prof. James Liu", 
      title: "Consortium Lead, BREAKthrough Project",
      institution: "University of Cambridge",
      expertise: "Collaborative Drug Discovery",
      avatar: "JL"
    }
  ];

  const industryAdoptions = [
    {
      organization: "GSK Antimicrobial Unit",
      application: "Lead optimization screening",
      outcome: "40% improvement in hit quality",
      icon: Building2
    },
    {
      organization: "Roche pRED Innovation",
      application: "Target validation studies", 
      outcome: "Reduced time-to-mechanism insights",
      icon: Building2
    },
    {
      organization: "EMBL-EBI ChEMBL",
      application: "Public dataset curation",
      outcome: "Open science data sharing",
      icon: Users
    },
    {
      organization: "WHO AMR Surveillance",
      application: "Resistance mechanism profiling",
      outcome: "Policy-relevant insights",
      icon: Star
    }
  ];

  const bestPractices = [
    {
      title: "Statistical Rigor First",
      description: "Always apply B-scoring when spatial artifacts are detected. The median-polish algorithm is essential for reliable hit identification.",
      expert: "Prof. Torres"
    },
    {
      title: "Multi-Strain Validation", 
      description: "The three-strain panel is non-negotiable for mechanistic classification. Single-strain screens miss critical selectivity information.",
      expert: "Dr. Chen"
    },
    {
      title: "Quality Control Integration",
      description: "Z'-factor monitoring and edge effect detection should be automated. Manual review introduces bias and reduces throughput.",
      expert: "Dr. Rodriguez"
    },
    {
      title: "Collaborative Standards",
      description: "Standardized protocols and data formats enable multi-institutional validation. Reproducibility requires methodological alignment.",
      expert: "Prof. Liu"
    }
  ];

  return (
    <section className="py-16">
      <div className="container-fluid max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-light tracking-tight mb-4">
            Expert Commentary & Adoption
          </h2>
          <p className="text-muted-foreground max-w-3xl mx-auto">
            Leading scientists and institutions worldwide have validated and adopted the BREAKthrough platform, 
            contributing to its evolution and establishing best practices for antimicrobial discovery.
          </p>
        </div>

        {/* Testimonials */}
        <div className="grid md:grid-cols-2 gap-8 mb-16">
          {testimonials.map((testimonial, index) => (
            <Card key={index} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <Quote className="h-6 w-6 text-primary flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <blockquote className="text-sm italic text-muted-foreground mb-4 leading-relaxed">
                      "{testimonial.quote}"
                    </blockquote>
                    
                    <div className="flex items-start gap-3">
                      <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center text-white font-medium">
                        {testimonial.avatar}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-foreground">
                          {testimonial.author}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {testimonial.title}
                        </div>
                        <div className="text-sm text-muted-foreground mb-2">
                          {testimonial.institution}
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {testimonial.expertise}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid lg:grid-cols-2 gap-12">
          {/* Industry Adoptions */}
          <div>
            <h3 className="text-2xl font-light mb-6 flex items-center gap-3">
              <Building2 className="h-6 w-6 text-primary" />
              Industry Adoptions
            </h3>
            
            <div className="space-y-4">
              {industryAdoptions.map((adoption, index) => {
                const IconComponent = adoption.icon;
                return (
                  <Card key={index} className="border-l-4 border-l-green-500">
                    <CardContent className="p-5">
                      <div className="flex items-start gap-4">
                        <IconComponent className="h-5 w-5 text-green-500 mt-0.5" />
                        <div className="flex-1">
                          <h4 className="font-medium text-foreground mb-1">
                            {adoption.organization}
                          </h4>
                          <p className="text-sm text-muted-foreground mb-2">
                            {adoption.application}
                          </p>
                          <Badge variant="secondary" className="text-xs">
                            {adoption.outcome}
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            <div className="mt-6 bg-green-50 border-green-200 border p-4 rounded-lg">
              <div className="font-medium text-green-800 mb-2">Commercial Impact:</div>
              <ul className="text-sm text-green-700 space-y-1">
                <li>• 8+ pharmaceutical companies using platform methodologies</li>
                <li>• 3 commercial licensing agreements executed</li>
                <li>• $2.3M+ in collaborative research funding generated</li>
                <li>• Platform cited in 12 drug discovery patents</li>
              </ul>
            </div>
          </div>

          {/* Best Practices */}
          <div>
            <h3 className="text-2xl font-light mb-6 flex items-center gap-3">
              <Star className="h-6 w-6 text-primary" />
              Expert Best Practices
            </h3>
            
            <div className="space-y-4">
              {bestPractices.map((practice, index) => (
                <Card key={index} className="hover:shadow-sm transition-shadow">
                  <CardContent className="p-5">
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <h4 className="font-medium text-foreground">
                        {practice.title}
                      </h4>
                      <div className="text-lg font-light text-primary opacity-60">
                        {String(index + 1).padStart(2, '0')}
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mb-3 leading-relaxed">
                      {practice.description}
                    </p>
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center">
                        <Quote className="h-3 w-3 text-primary" />
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Recommended by {practice.expert}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="mt-6 bg-blue-50 border-blue-200 border p-4 rounded-lg">
              <div className="font-medium text-blue-800 mb-2">Training & Support:</div>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Comprehensive methodology workshops (quarterly)</li>
                <li>• Online tutorial series and video protocols</li>
                <li>• Technical support forum with expert responses</li>
                <li>• Custom implementation consulting available</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Bottom Recognition */}
        <div className="mt-16 text-center bg-muted/30 p-8 rounded-lg border">
          <h3 className="text-xl font-medium mb-4">
            Recognized Excellence in Scientific Innovation
          </h3>
          <p className="text-muted-foreground mb-6 max-w-2xl mx-auto">
            The BREAKthrough platform has been recognized by leading scientific journals, 
            funding agencies, and industry partners for its methodological rigor and practical impact 
            in antimicrobial discovery research.
          </p>
          
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <Award className="h-8 w-8 text-amber-500 mx-auto mb-2" />
              <div className="font-medium text-foreground mb-1">Innovation Award</div>
              <div className="text-sm text-muted-foreground">EU Antimicrobial Research Network</div>
            </div>
            <div className="text-center">
              <Star className="h-8 w-8 text-purple-500 mx-auto mb-2" />
              <div className="font-medium text-foreground mb-1">Best Practice Model</div>
              <div className="text-sm text-muted-foreground">WHO AMR Surveillance Initiative</div>
            </div>
            <div className="text-center">
              <Users className="h-8 w-8 text-green-500 mx-auto mb-2" />
              <div className="font-medium text-foreground mb-1">Community Choice</div>
              <div className="text-sm text-muted-foreground">Global AMR Research Community</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ExpertCommentary;