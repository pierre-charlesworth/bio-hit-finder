import React from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { HelpCircle } from "lucide-react";

interface ScientificTooltipProps {
  term: string;
  definition: string;
  formula?: string;
  children?: React.ReactNode;
  className?: string;
}

const scientificTerms = {
  "LPS": {
    definition: "Lipopolysaccharide - Essential Gram-negative outer membrane component that creates a barrier to antibiotics",
    formula: "Core oligosaccharide + O-antigen + Lipid A"
  },
  "σE": {
    definition: "Sigma-E - Extracytoplasmic stress response sigma factor activated during envelope damage",
    formula: "RNA polymerase + σE → stress gene transcription"
  },
  "Cpx": {
    definition: "Two-component system sensing envelope stress and misfolded proteins in the periplasm",
    formula: "CpxA (sensor) + CpxR (regulator) → stress response"
  },
  "MAD": {
    definition: "Median Absolute Deviation - Robust measure of statistical dispersion resistant to outliers",
    formula: "MAD = median(|xi - median(x)|) × 1.4826"
  },
  "B-scoring": {
    definition: "Median-polish algorithm for correcting row/column systematic bias in plate-based screens",
    formula: "B-score = (value - row_median - col_median + plate_median) / MAD"
  },
  "Z'-factor": {
    definition: "Statistical measure of assay quality and signal separation (0.5-1.0 excellent, 0.3-0.5 acceptable)",
    formula: "Z' = 1 - (3 × (σp + σn)) / |μp - μn|"
  },
  "lptA": {
    definition: "LPS Transport Protein A - Periplasmic bridge connecting inner and outer membrane LPS transport complexes",
    formula: "LptC ↔ LptA ↔ LptDE complex"
  },
  "ldtD": {
    definition: "L,D-Transpeptidase D - Forms 3-3 crosslinks in peptidoglycan matrix during envelope stress",
    formula: "Peptidoglycan + ldtD → 3-3 crosslinked peptidoglycan"
  },
  "ΔtolC": {
    definition: "TolC efflux pump deletion strain with increased outer membrane permeability",
    formula: "Wild-type sensitivity + ΔtolC = enhanced compound penetration"
  },
  "BetaGlo": {
    definition: "ATP-based luciferase assay using 6-O-β-galactopyranosyl-luciferin substrate",
    formula: "β-galactosidase + substrate → D-luciferin + luciferase → light"
  },
  "BacTiter": {
    definition: "Metabolic activity assay measuring cellular ATP levels using D-luciferin",
    formula: "Cellular ATP + D-luciferin + luciferase → oxyluciferin + light"
  },
  "Moran's I": {
    definition: "Spatial correlation statistic used to detect clustering and edge effects in plate data",
    formula: "I = (n/W) × Σ(wij(xi - x̄)(xj - x̄)) / Σ(xi - x̄)²"
  }
};

const ScientificTooltip: React.FC<ScientificTooltipProps> = ({ 
  term, 
  definition, 
  formula, 
  children, 
  className = "" 
}) => {
  // Use predefined definition if available, otherwise use provided definition
  const termData = scientificTerms[term as keyof typeof scientificTerms] || { definition, formula };
  
  return (
    <TooltipProvider>
      <Tooltip delayDuration={200}>
        <TooltipTrigger asChild>
          {children ? (
            <span className={`underline decoration-dotted decoration-primary cursor-help ${className}`}>
              {children}
            </span>
          ) : (
            <span className={`inline-flex items-center gap-1 underline decoration-dotted decoration-primary cursor-help ${className}`}>
              {term}
              <HelpCircle className="h-3 w-3 text-muted-foreground" />
            </span>
          )}
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">
          <div className="space-y-2">
            <div className="font-medium text-foreground">{term}</div>
            <div className="text-sm text-muted-foreground">
              {termData.definition}
            </div>
            {termData.formula && (
              <div className="text-xs font-mono bg-muted p-2 rounded border">
                {termData.formula}
              </div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default ScientificTooltip;
export { scientificTerms };