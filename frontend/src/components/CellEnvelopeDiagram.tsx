import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Info, Play, Pause } from 'lucide-react';
import ScientificTooltip from '@/components/ui/scientific-tooltip';

interface CellComponent {
  id: string;
  name: string;
  description: string;
  function: string;
  reporterConnection: string;
  coordinates: {
    top: string;
    left: string;
    width: string;
    height: string;
  };
  color: string;
}

const CellEnvelopeDiagram = () => {
  const [selectedComponent, setSelectedComponent] = useState<string | null>(null);
  const [hoveredComponent, setHoveredComponent] = useState<string | null>(null);
  const [isAutoTourActive, setIsAutoTourActive] = useState(false);
  const [tourStep, setTourStep] = useState(0);

  const cellComponents: CellComponent[] = [
    {
      id: 'lps',
      name: 'Lipopolysaccharide (LPS)',
      description: 'Complex glycolipids forming the outer leaflet of the outer membrane',
      function: 'Primary antibiotic permeability barrier, endotoxin activity',
      reporterConnection: '<em>lptA</em> reporter detects disruption of LPS transport and assembly',
      coordinates: { top: '0%', left: '8%', width: '84%', height: '15%' },
      color: 'bg-green-500/30 border-green-500'
    },
    {
      id: 'porin',
      name: 'Porin Channels',
      description: 'β-barrel proteins allowing selective permeability',
      function: 'Controlled passage of small molecules across outer membrane',
      reporterConnection: 'Porin function affects compound penetration and <em>lptA</em> stress response',
      coordinates: { top: '15%', left: '42%', width: '16%', height: '30%' },
      color: 'bg-pink-500/30 border-pink-500'
    },
    {
      id: 'outer-membrane',
      name: 'Outer Membrane',
      description: 'Asymmetric lipid bilayer with unique LPS outer leaflet',
      function: 'Selective permeability barrier, first line of defense',
      reporterConnection: 'Primary target for outer membrane permeabilizers detected by <em>lptA</em>',
      coordinates: { top: '30%', left: '0%', width: '100%', height: '10%' },
      color: 'bg-blue-500/30 border-blue-500'
    },
    {
      id: 'lipoprotein',
      name: 'Lipoproteins',
      description: 'Anchored proteins connecting outer membrane to peptidoglycan',
      function: 'Structural support and envelope integrity maintenance',
      reporterConnection: 'Bridge between OM and PG layers, affects both <em>lptA</em> and <em>ldtD</em> responses',
      coordinates: { top: '38%', left: '12%', width: '76%', height: '8%' },
      color: 'bg-yellow-500/30 border-yellow-500'
    },
    {
      id: 'periplasm',
      name: 'Periplasmic Space',
      description: 'Compartment between outer and inner membranes',
      function: 'Houses folding machinery, binding proteins, and stress sensors',
      reporterConnection: '<em>lptA</em> protein bridges LPS transport across this space',
      coordinates: { top: '40%', left: '5%', width: '90%', height: '25%' },
      color: 'bg-cyan-500/20 border-cyan-500'
    },
    {
      id: 'peptidoglycan',
      name: 'Peptidoglycan Layer',
      description: 'Cross-linked polymer mesh providing structural integrity',
      function: 'Maintains cell shape, prevents osmotic lysis',
      reporterConnection: '<em>ldtD</em> reporter activates when this layer requires reinforcement',
      coordinates: { top: '55%', left: '8%', width: '84%', height: '10%' },
      color: 'bg-red-500/30 border-red-500'
    },
    {
      id: 'inner-membrane',
      name: 'Inner Membrane',
      description: 'Symmetric phospholipid bilayer with embedded proteins',
      function: 'Energy production, active transport, protein secretion',
      reporterConnection: 'Houses stress response machinery that regulates <em>lptA</em> and <em>ldtD</em>',
      coordinates: { top: '75%', left: '0%', width: '100%', height: '10%' },
      color: 'bg-purple-500/30 border-purple-500'
    },
    {
      id: 'cytoplasm',
      name: 'Cytoplasm',
      description: 'Internal cellular space containing genetic material and ribosomes',
      function: 'Metabolic processes, transcription, translation',
      reporterConnection: 'Site of <em>lptA</em> and <em>ldtD</em> transcription and reporter protein synthesis',
      coordinates: { top: '85%', left: '5%', width: '90%', height: '15%' },
      color: 'bg-orange-500/20 border-orange-500'
    }
  ];

  const selectedInfo = selectedComponent ? cellComponents.find(c => c.id === selectedComponent) : null;
  const hoveredInfo = hoveredComponent ? cellComponents.find(c => c.id === hoveredComponent) : null;

  const startAutoTour = () => {
    setIsAutoTourActive(true);
    setTourStep(0);
    setSelectedComponent(cellComponents[0].id);
  };

  const stopAutoTour = () => {
    setIsAutoTourActive(false);
    setTourStep(0);
  };

  React.useEffect(() => {
    if (isAutoTourActive && tourStep < cellComponents.length) {
      const timer = setTimeout(() => {
        if (tourStep < cellComponents.length - 1) {
          setTourStep(tourStep + 1);
          setSelectedComponent(cellComponents[tourStep + 1].id);
        } else {
          setIsAutoTourActive(false);
          setTourStep(0);
        }
      }, 3000);
      
      return () => clearTimeout(timer);
    }
  }, [isAutoTourActive, tourStep]);

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex justify-center gap-4">
        <Button
          onClick={isAutoTourActive ? stopAutoTour : startAutoTour}
          variant="outline"
          size="sm"
          className="gap-2"
        >
          {isAutoTourActive ? (
            <>
              <Pause className="h-4 w-4" />
              Stop Tour
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              Guided Tour
            </>
          )}
        </Button>
        <Button
          onClick={() => {
            setSelectedComponent(null);
            setHoveredComponent(null);
            stopAutoTour();
          }}
          variant="ghost"
          size="sm"
        >
          Clear Selection
        </Button>
      </div>

      {/* Main Interactive Diagram */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Image with Interactive Areas */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg text-center">
                Gram-negative Bacterial Cell Envelope
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative w-full max-w-2xl mx-auto">
                {/* Background Image */}
                <img
                  src="/cell-envelope-diagram.jpeg"
                  alt="Gram-negative Bacterial Cell Envelope"
                  className="w-full h-auto rounded-lg"
                />
                
                {/* Interactive Clickable Areas */}
                {cellComponents.map((component) => (
                  <button
                    key={component.id}
                    className={`
                      absolute cursor-pointer transition-all duration-200
                      ${hoveredComponent === component.id ? 'z-20' : 'z-10'}
                    `}
                    style={{
                      top: component.coordinates.top,
                      left: component.coordinates.left,
                      width: component.coordinates.width,
                      height: component.coordinates.height,
                    }}
                    onClick={() => setSelectedComponent(component.id)}
                    onMouseEnter={() => setHoveredComponent(component.id)}
                    onMouseLeave={() => setHoveredComponent(null)}
                    aria-label={`Select ${component.name}`}
                  />
                ))}

                {/* Hover Overlay */}
                {hoveredComponent && (
                  <div
                    className={`
                      absolute pointer-events-none transition-all duration-200
                      ${cellComponents.find(c => c.id === hoveredComponent)?.color} 
                      border-2 rounded-sm opacity-60 z-15
                    `}
                    style={{
                      top: cellComponents.find(c => c.id === hoveredComponent)?.coordinates.top,
                      left: cellComponents.find(c => c.id === hoveredComponent)?.coordinates.left,
                      width: cellComponents.find(c => c.id === hoveredComponent)?.coordinates.width,
                      height: cellComponents.find(c => c.id === hoveredComponent)?.coordinates.height,
                    }}
                  />
                )}

                {/* Selection Overlay */}
                {selectedComponent && (
                  <div
                    className={`
                      absolute pointer-events-none transition-all duration-300
                      ${cellComponents.find(c => c.id === selectedComponent)?.color}
                      border-2 rounded-sm animate-pulse z-25
                    `}
                    style={{
                      top: cellComponents.find(c => c.id === selectedComponent)?.coordinates.top,
                      left: cellComponents.find(c => c.id === selectedComponent)?.coordinates.left,
                      width: cellComponents.find(c => c.id === selectedComponent)?.coordinates.width,
                      height: cellComponents.find(c => c.id === selectedComponent)?.coordinates.height,
                    }}
                  />
                )}
              </div>
              
              {/* Quick Info Display */}
              {(hoveredInfo && !selectedInfo) && (
                <div className="mt-4 p-3 bg-muted/50 rounded-lg border">
                  <div className="font-medium text-sm">{hoveredInfo.name}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Click to learn more
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Information Panel */}
        <div className="lg:col-span-1">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Info className="h-5 w-5" />
                Component Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              {selectedInfo ? (
                <div className="space-y-4">
                  <div>
                    <Badge variant="outline" className="mb-3">
                      {selectedInfo.name}
                    </Badge>
                    <p className="text-sm text-muted-foreground">
                      {selectedInfo.description}
                    </p>
                  </div>
                  
                  <div>
                    <div className="text-sm font-medium text-foreground mb-1">Biological Function:</div>
                    <p className="text-sm text-muted-foreground">
                      {selectedInfo.function}
                    </p>
                  </div>
                  
                  <div>
                    <div className="text-sm font-medium text-foreground mb-1">Reporter Connection:</div>
                    <p className="text-sm text-muted-foreground">
                      <span dangerouslySetInnerHTML={{ __html: selectedInfo.reporterConnection }} />
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center text-muted-foreground py-8">
                  <Info className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-sm">
                    Click on any part of the cell envelope to learn about its structure and role in the screening platform.
                  </p>
                  {isAutoTourActive && (
                    <div className="mt-4">
                      <Badge variant="secondary">
                        Tour Step {tourStep + 1} of {cellComponents.length}
                      </Badge>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Reporter Systems Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Dual-Reporter System Integration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="border rounded-lg p-4">
              <div className="font-medium text-red-600 mb-2">
                <ScientificTooltip term="lptA">
                  <span dangerouslySetInnerHTML={{ __html: '<em>lptA</em> Reporter System' }} />
                </ScientificTooltip>
              </div>
              <div className="text-sm text-muted-foreground mb-2">
                <strong>Pathway:</strong> σE Stress Response
              </div>
              <div className="text-sm text-muted-foreground mb-2">
                <strong>Trigger:</strong> LPS transport disruption
              </div>
              <div className="text-sm text-muted-foreground">
                Using both <ScientificTooltip term="lptA"><span dangerouslySetInnerHTML={{ __html: '<em>lptA</em>' }} /></ScientificTooltip> and{' '}
                <ScientificTooltip term="ldtD"><span dangerouslySetInnerHTML={{ __html: '<em>ldtD</em>' }} /></ScientificTooltip> reporters provides 
                comprehensive envelope stress detection across multiple cellular compartments.
              </div>
            </div>
            
            <div className="border rounded-lg p-4">
              <div className="font-medium text-green-600 mb-2">
                <ScientificTooltip term="ldtD">
                  <span dangerouslySetInnerHTML={{ __html: '<em>ldtD</em> Reporter System' }} />
                </ScientificTooltip>
              </div>
              <div className="text-sm text-muted-foreground mb-2">
                <strong>Pathway:</strong> Cpx Stress Response
              </div>
              <div className="text-sm text-muted-foreground mb-2">
                <strong>Trigger:</strong> Peptidoglycan damage/stress
              </div>
              <div className="text-sm text-muted-foreground">
                This dual approach enables mechanism-specific compound classification and reduces false positives in outer membrane permeabilizer identification.
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CellEnvelopeDiagram;