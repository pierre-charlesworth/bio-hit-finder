import React from 'react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { HelpCircle } from "lucide-react";
import { InlineMath, BlockMath } from 'react-katex';
import 'katex/dist/katex.min.css';

interface ScientificTooltipProps {
  term: string;
  definition: string;
  formula?: string;
  latexFormula?: string;
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
    formula: "MAD = median(|xi - median(x)|) × 1.4826",
    latexFormula: "\\text{MAD} = \\text{median}(|x_i - \\text{median}(x)|) \\times 1.4826"
  },
  "B-scoring": {
    definition: "Median-polish algorithm for correcting row/column systematic bias in plate-based screens",
    formula: "B-score = (value - row_median - col_median + plate_median) / MAD",
    latexFormula: "B = \\frac{x_{ij} - r_i - c_j + \\mu}{\\text{MAD}}"
  },
  "Z'-factor": {
    definition: "Statistical measure of assay quality and signal separation (0.5-1.0 excellent, 0.3-0.5 acceptable)",
    formula: "Z' = 1 - (3 × (σp + σn)) / |μp - μn|",
    latexFormula: "Z' = 1 - \\frac{3(\\sigma_p + \\sigma_n)}{|\\mu_p - \\mu_n|}"
  },
  "lptA": {
    definition: "LPS Transport Protein A - Essential periplasmic component of the Lpt system forming a β-jellyroll bridge between inner and outer membrane LPS transport complexes. σE-regulated reporter for outer membrane permeabilization and LPS transport disruption. Upregulated when compounds compromise the outer membrane permeability barrier or interfere with Lpt system function.",
    formula: "σE activation → lptA transcription ↑ (LPS stress response)"
  },
  "ldtD": {
    definition: "L,D-Transpeptidase D - Periplasmic enzyme catalyzing 3-3 cross-links in peptidoglycan during envelope stress. Cpx-regulated reporter for peptidoglycan remodeling and envelope reinforcement responses. Activated when cells require structural stabilization against envelope-damaging compounds or osmotic stress.",
    formula: "Cpx activation → ldtD transcription ↑ (peptidoglycan stress response)"
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
    formula: "I = (n/W) × Σ(wij(xi - x̄)(xj - x̄)) / Σ(xi - x̄)²",
    latexFormula: "I = \\frac{n}{W} \\cdot \\frac{\\sum_{i}\\sum_{j} w_{ij}(x_i - \\bar{x})(x_j - \\bar{x})}{\\sum_{i}(x_i - \\bar{x})^2}"
  },
  "dual-reporter": {
    definition: "Dual-reporter screening system using both lptA and ldtD promoter-reporter fusions to detect orthogonal envelope stress responses. lptA captures outer membrane/LPS-specific stress (σE pathway), while ldtD detects peptidoglycan/periplasmic stress (Cpx pathway), enabling mechanism-specific compound classification.",
    formula: "lptA (σE) + ldtD (Cpx) → envelope stress mechanism discrimination"
  },
  "envelope stress": {
    definition: "Cellular response to damage or disruption of the bacterial cell envelope (outer membrane, peptidoglycan, inner membrane). Activates specific stress response pathways (σE, Cpx, Rcs) that upregulate protective genes and repair systems. Key target for antibiotic and permeabilizer development.",
    formula: "Envelope damage → stress sensors → transcriptional response → protective gene expression"
  },
  "outer membrane permeabilizer": {
    definition: "Compounds that specifically disrupt the Gram-negative outer membrane permeability barrier without necessarily killing the cell. Enable antibiotic synergy by allowing normally excluded drugs to penetrate the outer membrane. Detected by lptA/ldtD reporter activation and ΔtolC strain sensitivity patterns.",
    formula: "OM permeabilizer + antibiotic → enhanced antimicrobial activity"
  }
};

const ScientificTooltip: React.FC<ScientificTooltipProps> = ({ 
  term, 
  definition, 
  formula,
  latexFormula, 
  children, 
  className = "" 
}) => {
  // Use predefined definition if available, otherwise use provided definition
  const termData = scientificTerms[term as keyof typeof scientificTerms] || { definition, formula, latexFormula };
  
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
            {(termData.latexFormula || termData.formula) && (
              <div className="bg-muted p-3 rounded border">
                {termData.latexFormula ? (
                  <div className="text-center">
                    <BlockMath math={termData.latexFormula} />
                  </div>
                ) : (
                  <div className="text-xs font-mono">
                    {termData.formula}
                  </div>
                )}
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