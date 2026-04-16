<template>
  <div>
    <h1 class="text-2xl font-bold text-white mb-6">Dashboard</h1>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      <div class="bg-gray-900 rounded-lg p-4 border border-gray-800">
        <div class="text-sm text-gray-400">Total Predictions</div>
        <div class="text-3xl font-bold text-white mt-1">{{ summary?.total_predictions || 0 }}</div>
      </div>
      <div class="bg-gray-900 rounded-lg p-4 border border-gray-800">
        <div class="text-sm text-gray-400">Active Signals</div>
        <div class="text-3xl font-bold text-green-400 mt-1">{{ summary?.active_signals || 0 }}</div>
      </div>
      <div class="bg-gray-900 rounded-lg p-4 border border-gray-800">
        <div class="text-sm text-gray-400">5-Day Accuracy</div>
        <div class="text-3xl font-bold mt-1" :class="accuracyColor">
          {{ summary?.accuracy_rate != null ? `${summary.accuracy_rate.toFixed(1)}%` : 'N/A' }}
        </div>
        <div class="text-xs text-gray-500">{{ summary?.accuracy_count || 0 }} evaluated</div>
      </div>
      <div class="bg-gray-900 rounded-lg p-4 border border-gray-800">
        <div class="text-sm text-gray-400">Scheduler</div>
        <div class="flex items-center mt-2">
          <span
            class="w-2 h-2 rounded-full mr-2"
            :class="summary?.scheduler_status?.running ? 'bg-green-400' : 'bg-red-400'"
          />
          <span class="text-sm text-white">
            {{ summary?.scheduler_status?.running ? 'Running' : 'Stopped' }}
          </span>
        </div>
        <div v-if="nextRun" class="text-xs text-gray-500 mt-1">Next: {{ nextRun }}</div>
      </div>
    </div>

    <!-- Top Signals -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-gray-900 rounded-lg border border-gray-800">
        <div class="px-4 py-3 border-b border-gray-800">
          <h2 class="text-lg font-semibold text-white">Top Signals</h2>
          <p class="text-xs text-gray-400">Highest confidence current predictions</p>
        </div>
        <div class="divide-y divide-gray-800">
          <div
            v-for="signal in summary?.top_signals || []"
            :key="signal.id"
            class="px-4 py-3 hover:bg-gray-800/50 cursor-pointer"
            @click="$router.push(`/predictions/${signal.id}`)"
          >
            <div class="flex items-center justify-between">
              <div>
                <span class="font-mono font-bold text-white text-lg">{{ signal.ticker }}</span>
                <span class="text-gray-500 text-sm ml-2">${{ signal.price_at_prediction.toFixed(2) }}</span>
              </div>
              <SignalBadge :signal="signal.signal" />
            </div>
            <div class="text-sm text-gray-400 mt-1">{{ signal.chain_narrative }}</div>
            <div class="flex items-center gap-4 mt-2">
              <ConfidenceMeter :confidence="signal.confidence" />
              <ChainDepthIndicator :depth="signal.chain_depth" />
            </div>
          </div>
          <div v-if="!summary?.top_signals?.length" class="px-4 py-8 text-center text-gray-500">
            No signals yet. Trigger a research cycle to get started.
          </div>
        </div>
      </div>

      <!-- Recent Predictions -->
      <div class="bg-gray-900 rounded-lg border border-gray-800">
        <div class="px-4 py-3 border-b border-gray-800">
          <h2 class="text-lg font-semibold text-white">Recent Predictions</h2>
          <p class="text-xs text-gray-400">Latest chain-of-effects discoveries</p>
        </div>
        <div class="divide-y divide-gray-800">
          <div
            v-for="pred in summary?.recent_predictions || []"
            :key="pred.id"
            class="px-4 py-3 hover:bg-gray-800/50 cursor-pointer"
            @click="$router.push(`/predictions/${pred.id}`)"
          >
            <div class="flex items-center justify-between">
              <div>
                <span class="font-mono font-bold text-white">{{ pred.ticker }}</span>
                <SignalBadge :signal="pred.signal" class="ml-2" />
              </div>
              <span class="text-xs text-gray-500">{{ formatDate(pred.created_at) }}</span>
            </div>
            <div class="text-sm text-gray-400 mt-1 line-clamp-2">{{ pred.why_most_miss_it }}</div>
          </div>
          <div v-if="!summary?.recent_predictions?.length" class="px-4 py-8 text-center text-gray-500">
            No predictions yet.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { DashboardSummary } from '../types'
import { getDashboard } from '../api/client'
import SignalBadge from '../components/SignalBadge.vue'
import ConfidenceMeter from '../components/ConfidenceMeter.vue'
import ChainDepthIndicator from '../components/ChainDepthIndicator.vue'

const summary = ref<DashboardSummary | null>(null)

const accuracyColor = computed(() => {
  const rate = summary.value?.accuracy_rate
  if (rate == null) return 'text-gray-400'
  if (rate >= 60) return 'text-green-400'
  if (rate >= 40) return 'text-yellow-400'
  return 'text-red-400'
})

const nextRun = computed(() => {
  const jobs = summary.value?.scheduler_status?.jobs || []
  const upcoming = jobs
    .filter(j => j.next_run)
    .sort((a, b) => new Date(a.next_run!).getTime() - new Date(b.next_run!).getTime())
  if (upcoming.length > 0) {
    return new Date(upcoming[0].next_run!).toLocaleTimeString()
  }
  return null
})

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

onMounted(async () => {
  try {
    summary.value = await getDashboard()
  } catch (e) {
    console.error('Failed to load dashboard:', e)
  }
})
</script>
