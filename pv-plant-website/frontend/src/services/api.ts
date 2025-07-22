import axios, { AxiosInstance, AxiosResponse } from 'axios';

// API response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message: string;
  timestamp: string;
  error?: string;
  details?: any;
}

// Configuration types
export interface LocationConfig {
  latitude: number;
  longitude: number;
  elevation?: number;
  timezone?: string;
}

export interface SystemConfig {
  dc_capacity: number;
  module_type: string;
  inverter_type: string;
  modules_per_string: number;
  strings_per_inverter: number;
  system_voltage?: number;
}

export interface ArrayConfig {
  mounting_type: 'fixed' | 'single_axis' | 'dual_axis';
  tilt?: number;
  azimuth?: number;
  tracking_type?: string;
  gcr?: number;
  axis_tilt?: number;
  axis_azimuth?: number;
  max_angle?: number;
  backtrack?: boolean;
}

export interface LossConfig {
  soiling: number;
  shading: number;
  snow: number;
  mismatch: number;
  wiring: number;
  connections: number;
  lid: number;
  nameplate_rating: number;
  age: number;
  availability: number;
}

export interface SystemConfiguration {
  location: LocationConfig;
  system: SystemConfig;
  array: ArrayConfig;
  losses: LossConfig;
  name?: string;
  description?: string;
}

// Weather data types
export interface WeatherRequest {
  latitude: number;
  longitude: number;
  year?: number;
  source?: 'nsrdb' | 'pvgis' | 'auto';
  use_cache?: boolean;
}

export interface WeatherDataPoint {
  timestamp: string;
  ghi: number;
  dni: number;
  dhi: number;
  temp_air: number;
  wind_speed: number;
  relative_humidity?: number;
  pressure?: number;
}

// Simulation types
export interface SimulationOptions {
  year?: number;
  weather_source?: string;
  dc_model?: string;
  ac_model?: string;
  temperature_model?: string;
  clear_sky_model?: string;
  irradiance_model?: string;
  aoi_model?: string;
  spectral_model?: string;
  calculate_hourly?: boolean;
  calculate_daily?: boolean;
  calculate_monthly?: boolean;
  include_weather_data?: boolean;
}

export interface SimulationRequest {
  configuration_id: string;
  simulation_options?: SimulationOptions;
  name?: string;
  description?: string;
}

export interface SimulationStatus {
  simulation_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_step?: string;
  estimated_completion?: string;
  started_at?: string;
  updated_at: string;
}

// Results types
export interface SummaryMetrics {
  annual_energy: number;
  specific_yield: number;
  performance_ratio: number;
  capacity_factor: number;
  peak_power: number;
  energy_density: number;
}

export interface MonthlyData {
  month: number;
  energy: number;
  avg_power: number;
  peak_power: number;
  performance_ratio: number;
  capacity_factor: number;
  ghi_total: number;
  dni_total: number;
  dhi_total: number;
  avg_temperature: number;
}

export interface SimulationResults {
  simulation_id: string;
  configuration_id: string;
  created_at: string;
  summary: SummaryMetrics;
  monthly_data: MonthlyData[];
  weather_summary: any;
  system_performance: any;
  daily_data?: any[];
  hourly_data?: any[];
  calculation_time: number;
  data_size: number;
}

// Module and Inverter types
export interface ModuleInfo {
  name: string;
  technology: string;
  manufacturer: string;
  power_rating: number;
  efficiency: number;
  area: number;
  voltage_oc: number;
  current_sc: number;
  voltage_mp: number;
  current_mp: number;
  temperature_coeff_pmp: number;
  temperature_coeff_oc: number;
  temperature_coeff_sc: number;
  noct: number;
}

export interface InverterInfo {
  name: string;
  manufacturer: string;
  power_rating: number;
  efficiency: number;
  voltage_ac: number;
  voltage_dc_min: number;
  voltage_dc_max: number;
  voltage_dc_mppt_min: number;
  voltage_dc_mppt_max: number;
  current_dc_max: number;
  mppt_inputs: number;
}

export class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL || '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('API Response Error:', error);
        
        // Handle different error types
        if (error.response) {
          // Server responded with error status
          const { status, data } = error.response;
          console.error(`API Error ${status}:`, data);
        } else if (error.request) {
          // Network error
          console.error('Network Error:', error.request);
        } else {
          // Other error
          console.error('Error:', error.message);
        }
        
        return Promise.reject(error);
      }
    );
  }

  // System configuration endpoints
  async configureSystem(config: SystemConfiguration): Promise<ApiResponse> {
    const response = await this.client.post<ApiResponse>('/configure', config);
    return response.data;
  }

  async getModules(filters?: {
    technology?: string;
    manufacturer?: string;
    min_power?: number;
    max_power?: number;
  }): Promise<ApiResponse<{ modules: ModuleInfo[]; total_count: number }>> {
    const response = await this.client.get<ApiResponse>('/modules', { params: filters });
    return response.data;
  }

  async getInverters(filters?: {
    manufacturer?: string;
    min_power?: number;
    max_power?: number;
  }): Promise<ApiResponse<{ inverters: InverterInfo[]; total_count: number }>> {
    const response = await this.client.get<ApiResponse>('/inverters', { params: filters });
    return response.data;
  }

  // Weather data endpoints
  async getWeatherData(request: WeatherRequest): Promise<ApiResponse> {
    const { latitude, longitude, ...params } = request;
    const response = await this.client.get<ApiResponse>(`/weather/${latitude}/${longitude}`, { params });
    return response.data;
  }

  async testWeatherServices(): Promise<ApiResponse> {
    const response = await this.client.get<ApiResponse>('/weather/test');
    return response.data;
  }

  // Simulation endpoints
  async startSimulation(request: SimulationRequest): Promise<ApiResponse> {
    const response = await this.client.post<ApiResponse>('/simulate', request);
    return response.data;
  }

  async getSimulationStatus(simulationId: string): Promise<ApiResponse<SimulationStatus>> {
    const response = await this.client.get<ApiResponse>(`/simulate/${simulationId}/status`);
    return response.data;
  }

  async cancelSimulation(simulationId: string): Promise<ApiResponse> {
    const response = await this.client.delete<ApiResponse>(`/simulate/${simulationId}`);
    return response.data;
  }

  async getSimulations(page: number = 1, pageSize: number = 20): Promise<ApiResponse> {
    const response = await this.client.get<ApiResponse>('/simulate', {
      params: { page, page_size: pageSize }
    });
    return response.data;
  }

  // Results endpoints
  async getResults(simulationId: string): Promise<ApiResponse<SimulationResults>> {
    const response = await this.client.get<ApiResponse>(`/results/${simulationId}`);
    return response.data;
  }

  async exportResults(simulationId: string, format: string = 'csv', options?: {
    resolution?: string;
    include_weather?: boolean;
    include_metadata?: boolean;
  }): Promise<Blob> {
    const response = await this.client.get(`/export/${simulationId}`, {
      params: { format, ...options },
      responseType: 'blob'
    });
    return response.data;
  }

  // System info endpoints
  async getSystemInfo(): Promise<ApiResponse> {
    const response = await this.client.get<ApiResponse>('/info');
    return response.data;
  }

  async getHealthStatus(): Promise<ApiResponse> {
    const response = await this.client.get<ApiResponse>('/health');
    return response.data;
  }

  // Utility methods
  async downloadFile(simulationId: string, filename: string, format: string = 'csv'): Promise<void> {
    try {
      const blob = await this.exportResults(simulationId, format);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      
      // Trigger download
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      throw error;
    }
  }

  // WebSocket connection for real-time updates (future enhancement)
  connectWebSocket(simulationId: string, onMessage: (data: any) => void): WebSocket | null {
    try {
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/simulation/${simulationId}`;
      const ws = new WebSocket(wsUrl);
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onMessage(data);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      return ws;
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      return null;
    }
  }
}