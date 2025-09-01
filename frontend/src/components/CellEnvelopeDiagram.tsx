import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Info, Microscope, Target } from 'lucide-react';
import ScientificTooltip from '@/components/ui/scientific-tooltip';

const CellEnvelopeDiagram = () => {
  const [selectedComponent, setSelectedComponent] = useState<string | null>(null);

  const envelopeComponents = [
    {
      id: 'outer-membrane',
      name: 'Outer Membrane (OM)',
      description: 'Asymmetric lipid bilayer containing lipopolysaccharide (LPS) in the outer leaflet',
      function: 'Primary antibiotic barrier, contains porins for selective permeability',
      targets: 'lptA reporter detects disruption of LPS transport to this layer',
      position: { x: '10%', y: '20%', width: '80%', height: '8%' },
      color: 'bg-red-500'
    },
    {
      id: 'periplasm',
      name: 'Periplasmic Space',
      description: 'Compartment between inner and outer membranes containing periplasmic proteins',
      function: 'Houses protein folding machinery, nutrient binding proteins, and stress sensors',
      targets: 'lptA protein bridges LPS transport complexes across this space',
      position: { x: '15%', y: '32%', width: '70%', height: '20%' },
      color: 'bg-blue-300'
    },
    {
      id: 'peptidoglycan',
      name: 'Peptidoglycan Layer',
      description: 'Cross-linked polymer providing structural integrity to the cell',
      function: 'Maintains cell shape, prevents osmotic lysis, contains 4-3 and 3-3 crosslinks',
      targets: 'ldtD reporter activates when this layer requires structural reinforcement',
      position: { x: '20%', y: '38%', width: '60%', height: '6%' },
      color: 'bg-green-500'
    },
    {
      id: 'inner-membrane',
      name: 'Inner Membrane (IM)',
      description: 'Symmetric phospholipid bilayer containing transport and biosynthetic machinery',
      function: 'Energy generation, nutrient transport, protein secretion, LPS biosynthesis initiation',
      targets: 'Houses LptB-C complex that initiates LPS transport to outer membrane',
      position: { x: '10%', y: '54%', width: '80%', height: '8%' },
      color: 'bg-purple-500'
    },
    {
      id: 'cytoplasm',
      name: 'Cytoplasm',
      description: 'Interior of the bacterial cell containing genetic material and metabolic machinery',
      function: 'Site of transcription, translation, and cellular metabolism',
      targets: 'Location of reporter gene expression and stress response regulation',
      position: { x: '15%', y: '66%', width: '70%', height: '25%' },
      color: 'bg-yellow-300'
    }
  ];

  const reporterSystems = [
    {
      name: 'lptA Reporter',
      pathway: 'σE Stress Response',
      trigger: 'LPS transport disruption',
      location: 'Periplasm → OM transport',
      color: 'text-red-600'
    },
    {
      name: 'ldtD Reporter', 
      pathway: 'Cpx Stress Response',
      trigger: 'Peptidoglycan damage',
      location: 'Peptidoglycan crosslinking',
      color: 'text-green-600'
    }
  ];

  const selectedInfo = selectedComponent ? envelopeComponents.find(c => c.id === selectedComponent) : null;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Microscope className="h-5 w-5 text-primary" />
            Interactive Gram-Negative Cell Envelope
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Diagram */}
            <div className="relative">
              <div className="relative aspect-[4/5] border-2 border-muted rounded-lg overflow-hidden bg-gradient-to-b from-blue-50 to-blue-100">
                <div className="absolute inset-0 p-4">
                  <div className="text-xs text-muted-foreground mb-2 text-center">
                    Gram-Negative Bacterial Cell Envelope
                  </div>
                  
                  {/* Envelope Components */}
                  {envelopeComponents.map((component) => (
                    <div
                      key={component.id}
                      className={`absolute cursor-pointer transition-all duration-200 hover:opacity-80 border-2 border-white rounded ${component.color} ${
                        selectedComponent === component.id ? 'ring-2 ring-primary ring-offset-1' : ''
                      }`}
                      style={{
                        left: component.position.x,
                        top: component.position.y,
                        width: component.position.width,
                        height: component.position.height
                      }}
                      onClick={() => setSelectedComponent(
                        selectedComponent === component.id ? null : component.id
                      )}
                      title={component.name}
                    >
                      <div className="flex items-center justify-center h-full">
                        <span className="text-white text-xs font-medium text-center px-2">
                          {component.name}
                        </span>
                      </div>
                    </div>
                  ))}
                  
                  {/* Annotations */}
                  <div className="absolute top-2 right-2 text-xs">
                    <Badge variant="outline" className="bg-white">
                      <Target className="h-3 w-3 mr-1" />
                      Click components
                    </Badge>
                  </div>
                </div>
              </div>
              
              <div className="mt-4 text-center">
                <p className="text-sm text-muted-foreground">
                  Click on envelope components to learn about their role in antibiotic resistance and reporter systems
                </p>
              </div>
            </div>

            {/* Information Panel */}
            <div className="space-y-6">
              {selectedInfo ? (
                <Card className="border-l-4 border-l-primary">
                  <CardContent className="p-5">
                    <div className="flex items-start gap-3 mb-4">
                      <div className={`w-4 h-4 rounded ${selectedInfo.color} mt-0.5`}></div>
                      <div>
                        <h3 className="font-medium text-foreground mb-2">{selectedInfo.name}</h3>
                        <p className="text-sm text-muted-foreground mb-3">{selectedInfo.description}</p>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <div>
                        <div className="text-sm font-medium text-foreground mb-1">Biological Function:</div>
                        <p className="text-sm text-muted-foreground">{selectedInfo.function}</p>
                      </div>
                      
                      <div>
                        <div className="text-sm font-medium text-foreground mb-1">Reporter Targeting:</div>
                        <p className="text-sm text-muted-foreground">{selectedInfo.targets}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="border-dashed border-2">
                  <CardContent className="p-8 text-center">
                    <Info className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="font-medium text-foreground mb-2">Component Information</h3>
                    <p className="text-sm text-muted-foreground">
                      Click on any component in the diagram to learn about its structure, 
                      function, and role in the BREAKthrough screening platform.
                    </p>
                  </CardContent>
                </Card>
              )}

              {/* Reporter Systems Overview */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Dual-Reporter System</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {reporterSystems.map((reporter, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className={`font-medium ${reporter.color}`}>
                          <ScientificTooltip term={reporter.name.split(' ')[0]}>
                            {reporter.name}
                          </ScientificTooltip>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {reporter.pathway}
                        </Badge>
                      </div>
                      <div className="text-sm text-muted-foreground mb-2">
                        <strong>Trigger:</strong> {reporter.trigger}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        <strong>Location:</strong> {reporter.location}
                      </div>
                    </div>
                  ))}
                  
                  <div className="bg-primary/10 p-3 rounded border-l-4 border-l-primary">
                    <div className="text-sm font-medium text-foreground mb-1">
                      Why Dual Reporters?
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Using both <ScientificTooltip term="lptA">lptA</ScientificTooltip> and{' '}
                      <ScientificTooltip term="ldtD">ldtD</ScientificTooltip> reporters provides 
                      complementary readouts of envelope stress, enabling mechanistic classification 
                      and reducing false positives from non-specific effects.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CellEnvelopeDiagram;