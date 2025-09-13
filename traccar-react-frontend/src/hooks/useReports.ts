import { useState, useEffect, useCallback } from 'react';
import { API_ENDPOINTS, getAuthHeaders } from '../api/apiConfig';

export interface Report {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  report_type: 'route' | 'summary' | 'events' | 'stops' | 'trips' | 'maintenance' | 'fuel' | 'driver' | 'custom';
  format: 'json' | 'csv' | 'pdf' | 'xlsx';
  period: 'today' | 'yesterday' | 'this_week' | 'last_week' | 'this_month' | 'last_month' | 'this_year' | 'last_year' | 'custom';
  from_date?: string;
  to_date?: string;
  device_ids?: number[];
  group_ids?: number[];
  include_attributes?: boolean;
  include_addresses?: boolean;
  include_events?: boolean;
  include_geofences?: boolean;
  parameters?: Record<string, any>;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  completed_at?: string;
  file_path?: string;
  file_size?: number;
  error_message?: string;
}

export interface ReportTemplate {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  report_type: 'route' | 'summary' | 'events' | 'stops' | 'trips' | 'maintenance' | 'fuel' | 'driver' | 'custom';
  format: 'json' | 'csv' | 'pdf' | 'xlsx';
  parameters?: Record<string, any>;
  is_public: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReportStats {
  total_reports: number;
  reports_by_type: Record<string, number>;
  reports_by_status: Record<string, number>;
  total_file_size: number;
  last_generated?: string;
  most_used_type?: string;
}

export interface CreateReportData {
  name: string;
  description?: string;
  report_type: 'route' | 'summary' | 'events' | 'stops' | 'trips' | 'maintenance' | 'fuel' | 'driver' | 'custom';
  format?: 'json' | 'csv' | 'pdf' | 'xlsx';
  period?: 'today' | 'yesterday' | 'this_week' | 'last_week' | 'this_month' | 'last_month' | 'this_year' | 'last_year' | 'custom';
  from_date?: string;
  to_date?: string;
  device_ids?: number[];
  group_ids?: number[];
  include_attributes?: boolean;
  include_addresses?: boolean;
  include_events?: boolean;
  include_geofences?: boolean;
  parameters?: Record<string, any>;
}

export interface ReportListResponse {
  items: Report[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ReportTemplateListResponse {
  items: ReportTemplate[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export const useReports = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [stats, setStats] = useState<ReportStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch reports list
  const fetchReports = useCallback(async (params?: {
    page?: number;
    size?: number;
    report_type?: string;
    status?: string;
  }) => {
    setLoading(true);
    setError(null);

    try {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.size) queryParams.append('size', params.size.toString());
      if (params?.report_type) queryParams.append('report_type', params.report_type);
      if (params?.status) queryParams.append('status', params.status);

      const url = `${API_ENDPOINTS.REPORTS}?${queryParams.toString()}`;

      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch reports: ${response.statusText}`);
      }

      const data: ReportListResponse = await response.json();
      setReports(data.items);
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch reports';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Create a new report
  const createReport = useCallback(async (reportData: CreateReportData): Promise<Report> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(API_ENDPOINTS.REPORTS, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(reportData),
      });

      if (!response.ok) {
        throw new Error(`Failed to create report: ${response.statusText}`);
      }

      const newReport: Report = await response.json();
      setReports(prev => [newReport, ...prev]);
      return newReport;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create report';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get a specific report
  const getReport = useCallback(async (reportId: number): Promise<Report> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_ENDPOINTS.REPORTS}/${reportId}`, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to get report: ${response.statusText}`);
      }

      const report: Report = await response.json();
      return report;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get report';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Update a report
  const updateReport = useCallback(async (reportId: number, updateData: Partial<CreateReportData>): Promise<Report> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_ENDPOINTS.REPORTS}/${reportId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        throw new Error(`Failed to update report: ${response.statusText}`);
      }

      const updatedReport: Report = await response.json();
      setReports(prev => prev.map(r => r.id === reportId ? updatedReport : r));
      return updatedReport;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update report';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Delete a report
  const deleteReport = useCallback(async (reportId: number): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_ENDPOINTS.REPORTS}/${reportId}`, {
        method: 'DELETE',
        headers: {
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete report: ${response.statusText}`);
      }

      setReports(prev => prev.filter(r => r.id !== reportId));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete report';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get report data
  const getReportData = useCallback(async (reportId: number) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_ENDPOINTS.REPORTS}/${reportId}/data`, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to get report data: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get report data';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Download report
  const downloadReport = useCallback(async (reportId: number) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_ENDPOINTS.REPORTS}/${reportId}/download`, {
        headers: {
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to download report: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to download report';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch report statistics
  const fetchReportStats = useCallback(async (): Promise<ReportStats> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(API_ENDPOINTS.REPORT_STATS, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch report stats: ${response.statusText}`);
      }

      const statsData: ReportStats = await response.json();
      setStats(statsData);
      return statsData;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch report stats';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch report templates
  const fetchReportTemplates = useCallback(async (params?: {
    page?: number;
    size?: number;
    report_type?: string;
    public_only?: boolean;
  }): Promise<ReportTemplateListResponse> => {
    setLoading(true);
    setError(null);

    try {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.size) queryParams.append('size', params.size.toString());
      if (params?.report_type) queryParams.append('report_type', params.report_type);
      if (params?.public_only !== undefined) queryParams.append('public_only', params.public_only.toString());

      const url = `${API_ENDPOINTS.REPORT_TEMPLATES}?${queryParams.toString()}`;

      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch report templates: ${response.statusText}`);
      }

      const data: ReportTemplateListResponse = await response.json();
      setTemplates(data.items);
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch report templates';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    reports,
    templates,
    stats,
    loading,
    error,
    fetchReports,
    createReport,
    getReport,
    updateReport,
    deleteReport,
    getReportData,
    downloadReport,
    fetchReportStats,
    fetchReportTemplates,
  };
};
