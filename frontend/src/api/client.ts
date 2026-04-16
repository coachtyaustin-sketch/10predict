import axios from 'axios'
import type { DashboardSummary, AccuracyMetrics, Prediction, Signal } from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export async function getDashboard(): Promise<DashboardSummary> {
  const { data } = await api.get('/dashboard/summary')
  return data
}

export async function getAccuracy(): Promise<AccuracyMetrics> {
  const { data } = await api.get('/dashboard/accuracy')
  return data
}

export async function getPredictions(params?: {
  signal?: string
  ticker?: string
  min_confidence?: number
  page?: number
  per_page?: number
}): Promise<Signal[]> {
  const { data } = await api.get('/predictions', { params })
  return data
}

export async function getLatestPredictions(limit = 10): Promise<Signal[]> {
  const { data } = await api.get('/predictions/latest', { params: { limit } })
  return data
}

export async function getPrediction(id: number): Promise<Prediction> {
  const { data } = await api.get(`/predictions/${id}`)
  return data
}

export async function getSignals(params?: {
  signal_type?: string
  min_score?: number
  limit?: number
}): Promise<Signal[]> {
  const { data } = await api.get('/signals', { params })
  return data
}

export async function triggerResearch(cycleType = 'manual'): Promise<{ status: string; message: string }> {
  const { data } = await api.post('/research/trigger', null, { params: { cycle_type: cycleType } })
  return data
}

export async function getResearchStatus(): Promise<{ running: boolean }> {
  const { data } = await api.get('/research/status')
  return data
}

export async function getHealth(): Promise<any> {
  const { data } = await api.get('/health')
  return data
}
