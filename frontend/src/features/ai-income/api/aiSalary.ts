import api from '@/lib/axios';

export interface SalaryPredictionInput {
  currentSalary: number;
  kpiScore: number;
  softSkillScore: number;
  yearsExperience: number;
  certificationCount: number;
}

export interface SalaryPrediction {
  minSalary: number;
  medianSalary: number;
  maxSalary: number;
  changePercent: number;
  modelVersion: string;
  explanationMethod: string;
  contributions: { feature: string; impact: number; explanation: string }[];
  disclaimer: string;
}

export async function predictSalary(input: SalaryPredictionInput) {
  const { data } = await api.post<SalaryPrediction>('/ai-salary/simulate', input);
  return data;
}

export async function simulateBudget(input: { kpiWeight: number; tenureWeight: number; currentBudget: number }) {
  const { data } = await api.post<{ currentBudget: number; projectedBudget: number; changeAmount: number; modelVersion: string; disclaimer: string }>('/ai-salary/budget-simulation', input);
  return data;
}
