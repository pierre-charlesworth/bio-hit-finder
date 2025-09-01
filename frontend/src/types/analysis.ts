/**
 * Type definitions for multi-stage analysis
 */

export interface VitalityConfig {
  tolc_threshold: number;
  wt_threshold: number;
  sa_threshold: number;
}

export interface MultiStageConfig {
  z_threshold: number;
  viability_column: string;
  reporter_columns: string[];
  vitality_config: VitalityConfig;
  require_both_stages: boolean;
  include_partial_hits: boolean;
}

export interface AnalysisResult {
  success: boolean;
  results: WellResult[];
  summary: AnalysisSummary;
  total_wells: number;
  file_name: string;
  analysis_type?: string;
}

export interface WellResult {
  Well?: string;
  // Stage 1 - Reporter analysis
  Ratio_lptA?: number;
  Ratio_ldtD?: number;
  Z_lptA?: number;
  Z_ldtD?: number;
  Stage1_ReporterHit?: boolean;
  
  // Stage 2 - Vitality analysis  
  OD_WT?: number;
  OD_tolC?: number;
  OD_SA?: number;
  'WT%'?: number;
  'tolC%'?: number;
  'SA%'?: number;
  Stage2_VitalityHit?: boolean;
  VitalityPattern?: string;
  
  // Stage 3 - Platform hits
  Stage3_PlatformHit?: boolean;
  Stage3_HitType?: 'Full_Hit' | 'Partial_Reporter' | 'Partial_Vitality' | 'No_Hit';
  
  // Viability
  PassViab?: boolean;
}

export interface AnalysisSummary {
  total_wells: number;
  stage1_reporter_hits?: number;
  stage1_reporter_hit_rate?: number;
  stage2_vitality_hits?: number;
  stage2_vitality_hit_rate?: number;
  stage3_platform_hits?: number;
  stage3_platform_hit_rate?: number;
  dual_readout_detected?: boolean;
  hit_type_distribution?: Record<string, number>;
  vitality_hit_rate?: number;
  pattern_distribution?: Record<string, number>;
  percentage_statistics?: Record<string, any>;
  threshold_compliance?: Record<string, number>;
  config_used?: any;
}

export interface AnalysisState {
  isLoading: boolean;
  data: AnalysisResult | null;
  error: string | null;
  config: Partial<MultiStageConfig>;
}

export type AnalysisType = 'multi-stage' | 'vitality' | 'demo';