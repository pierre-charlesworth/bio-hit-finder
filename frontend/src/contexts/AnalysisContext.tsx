import React, { createContext, useContext, useState, ReactNode } from 'react';
import { AnalysisResult } from '@/types/analysis';

interface AnalysisContextType {
  currentAnalysis: AnalysisResult | null;
  isAnalyzing: boolean;
  analysisError: string | null;
  setCurrentAnalysis: (analysis: AnalysisResult | null) => void;
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
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const clearAnalysis = () => {
    setCurrentAnalysis(null);
    setAnalysisError(null);
    setIsAnalyzing(false);
  };

  const value: AnalysisContextType = {
    currentAnalysis,
    isAnalyzing,
    analysisError,
    setCurrentAnalysis,
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