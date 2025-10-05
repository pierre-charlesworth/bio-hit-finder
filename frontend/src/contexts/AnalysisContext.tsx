import React, { createContext, useContext, useState, useMemo, ReactNode } from 'react';
import { AnalysisResult } from '@/types/analysis';

interface AnalysisContextType {
  currentAnalysis: AnalysisResult | null;
  filteredAnalysis: AnalysisResult | null;
  selectedPlateId: string;
  availablePlates: string[];
  isAnalyzing: boolean;
  analysisError: string | null;
  setCurrentAnalysis: (analysis: AnalysisResult | null) => void;
  setSelectedPlateId: (plateId: string) => void;
  setIsAnalyzing: (analyzing: boolean) => void;
  setAnalysisError: (error: string | null) => void;
  clearAnalysis: () => void;
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

export const useAnalysis = () => {
  const context = useContext(AnalysisContext);
  if (context === undefined) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
};

interface AnalysisProviderProps {
  children: ReactNode;
}

export const AnalysisProvider: React.FC<AnalysisProviderProps> = ({ children }) => {
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResult | null>(null);
  const [selectedPlateId, setSelectedPlateId] = useState<string>('all');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Extract available plates from analysis data
  const availablePlates = useMemo(() => {
    if (!currentAnalysis?.results) return [];
    const plates = [...new Set(currentAnalysis.results.map((well: any) => well.PlateID || 'Unknown'))];
    return plates.sort();
  }, [currentAnalysis]);

  // Filter analysis data by selected plate
  const filteredAnalysis = useMemo(() => {
    if (!currentAnalysis || selectedPlateId === 'all') {
      return currentAnalysis;
    }

    const filteredResults = currentAnalysis.results.filter(
      (well: any) => well.PlateID === selectedPlateId
    );

    // Recalculate summary for filtered data
    const filteredSummary = {
      total_wells: filteredResults.length,
      stage1_reporter_hits: filteredResults.filter((w: any) => w.Stage1_ReporterHit).length,
      stage2_vitality_hits: filteredResults.filter((w: any) => w.Stage2_VitalityHit).length,
      stage3_platform_hits: filteredResults.filter((w: any) => w.Stage3_PlatformHit).length,
      stage1_reporter_hit_rate: filteredResults.length > 0
        ? filteredResults.filter((w: any) => w.Stage1_ReporterHit).length / filteredResults.length
        : 0,
      stage2_vitality_hit_rate: filteredResults.length > 0
        ? filteredResults.filter((w: any) => w.Stage2_VitalityHit).length / filteredResults.length
        : 0,
      stage3_platform_hit_rate: filteredResults.length > 0
        ? filteredResults.filter((w: any) => w.Stage3_PlatformHit).length / filteredResults.length
        : 0,
    };

    return {
      ...currentAnalysis,
      results: filteredResults,
      summary: filteredSummary,
      total_wells: filteredResults.length,
    };
  }, [currentAnalysis, selectedPlateId]);

  const clearAnalysis = () => {
    setCurrentAnalysis(null);
    setAnalysisError(null);
    setIsAnalyzing(false);
    setSelectedPlateId('all');
  };

  const value: AnalysisContextType = {
    currentAnalysis,
    filteredAnalysis,
    selectedPlateId,
    availablePlates,
    isAnalyzing,
    analysisError,
    setCurrentAnalysis,
    setSelectedPlateId,
    setIsAnalyzing,
    setAnalysisError,
    clearAnalysis,
  };

  return (
    <AnalysisContext.Provider value={value}>
      {children}
    </AnalysisContext.Provider>
  );
};