export interface HealthResponse {
  status: string;
  product: string;
}

export interface AnalyzeRequest {
  parcel_id?: string;
  address?: string;
  params?: Record<string, unknown>;
}

export interface AnalyzeResponse {
  parcel_id: string;
  feasibility: string;
  zoning: string;
  max_units: number;
  risks: string[];
  summary: string;
}
