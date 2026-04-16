export interface Prediction {
  id: number
  ticker: string
  signal: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL'
  score: number
  confidence: number
  chain_depth: number
  chain_narrative: string
  why_most_miss_it: string
  bull_case: string
  bear_case: string
  key_catalysts: string[]
  risk_factors: string[]
  price_at_prediction: number
  target_price_low: number | null
  target_price_high: number | null
  timeframe_days: number
  cycle_type: string
  report_text: string
  created_at: string
}

export interface Signal {
  id: number
  ticker: string
  signal: string
  score: number
  confidence: number
  chain_narrative: string
  why_most_miss_it: string
  price_at_prediction: number
  chain_depth: number
  created_at: string
}

export interface DashboardSummary {
  total_predictions: number
  active_signals: number
  accuracy_rate: number | null
  accuracy_count: number
  top_signals: Signal[]
  recent_predictions: Signal[]
  scheduler_status: {
    running: boolean
    jobs: { id: string; name: string; next_run: string | null }[]
  }
}

export interface AccuracyMetrics {
  total_evaluated: number
  direction_correct_1d: number | null
  direction_correct_3d: number | null
  direction_correct_5d: number | null
  significant_moves_hit: number | null
  avg_max_move_pct: number | null
}

export type SignalType = 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL'

export const SIGNAL_COLORS: Record<SignalType, string> = {
  STRONG_BUY: '#16a34a',
  BUY: '#22c55e',
  HOLD: '#6b7280',
  SELL: '#ef4444',
  STRONG_SELL: '#dc2626',
}

export const SIGNAL_LABELS: Record<SignalType, string> = {
  STRONG_BUY: 'Strong Buy',
  BUY: 'Buy',
  HOLD: 'Hold',
  SELL: 'Sell',
  STRONG_SELL: 'Strong Sell',
}
