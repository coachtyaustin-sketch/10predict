<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-white">Predictions</h1>
      <div class="flex gap-2">
        <select
          v-model="filterSignal"
          class="bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300"
        >
          <option value="">All Signals</option>
          <option value="STRONG_BUY">Strong Buy</option>
          <option value="BUY">Buy</option>
          <option value="HOLD">Hold</option>
          <option value="SELL">Sell</option>
          <option value="STRONG_SELL">Strong Sell</option>
        </select>
        <input
          v-model="filterTicker"
          placeholder="Filter by ticker..."
          class="bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 w-32"
        />
      </div>
    </div>

    <!-- Predictions Table -->
    <div class="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-800/50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Ticker</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Signal</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Score</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Confidence</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Chain</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Depth</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Price</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Date</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-800">
          <tr
            v-for="pred in predictions"
            :key="pred.id"
            class="hover:bg-gray-800/30 cursor-pointer"
            @click="$router.push(`/predictions/${pred.id}`)"
          >
            <td class="px-4 py-3 font-mono font-bold text-white">{{ pred.ticker }}</td>
            <td class="px-4 py-3"><SignalBadge :signal="pred.signal" /></td>
            <td class="px-4 py-3 text-sm" :class="pred.score > 0 ? 'text-green-400' : pred.score < 0 ? 'text-red-400' : 'text-gray-400'">
              {{ pred.score > 0 ? '+' : '' }}{{ pred.score.toFixed(1) }}
            </td>
            <td class="px-4 py-3"><ConfidenceMeter :confidence="pred.confidence" /></td>
            <td class="px-4 py-3 text-sm text-gray-400 max-w-xs truncate">{{ pred.chain_narrative }}</td>
            <td class="px-4 py-3"><ChainDepthIndicator :depth="pred.chain_depth" /></td>
            <td class="px-4 py-3 text-sm text-gray-300">${{ pred.price_at_prediction.toFixed(2) }}</td>
            <td class="px-4 py-3 text-sm text-gray-500">{{ formatDate(pred.created_at) }}</td>
          </tr>
          <tr v-if="!predictions.length">
            <td colspan="8" class="px-4 py-8 text-center text-gray-500">
              No predictions found. Try adjusting filters or trigger a research cycle.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import type { Signal } from '../types'
import { getPredictions } from '../api/client'
import SignalBadge from '../components/SignalBadge.vue'
import ConfidenceMeter from '../components/ConfidenceMeter.vue'
import ChainDepthIndicator from '../components/ChainDepthIndicator.vue'

const predictions = ref<Signal[]>([])
const filterSignal = ref('')
const filterTicker = ref('')

async function loadPredictions() {
  try {
    predictions.value = await getPredictions({
      signal: filterSignal.value || undefined,
      ticker: filterTicker.value || undefined,
      per_page: 50,
    })
  } catch (e) {
    console.error('Failed to load predictions:', e)
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric'
  })
}

watch([filterSignal, filterTicker], loadPredictions)
onMounted(loadPredictions)
</script>
