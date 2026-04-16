<template>
  <div v-if="prediction">
    <!-- Header -->
    <div class="flex items-center gap-4 mb-6">
      <button @click="$router.back()" class="text-gray-400 hover:text-white">Back</button>
      <h1 class="text-3xl font-mono font-bold text-white">{{ prediction.ticker }}</h1>
      <SignalBadge :signal="prediction.signal" />
      <span class="text-gray-400">${{ prediction.price_at_prediction.toFixed(2) }}</span>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Main Report -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Chain Narrative -->
        <div class="bg-gray-900 rounded-lg border border-gray-800 p-6">
          <h2 class="text-lg font-semibold text-purple-400 mb-2">Chain of Effects</h2>
          <div class="text-xl text-white font-medium mb-3">{{ prediction.chain_narrative }}</div>
          <ChainDepthIndicator :depth="prediction.chain_depth" />
        </div>

        <!-- Why Most Miss It -->
        <div class="bg-gray-900 rounded-lg border border-yellow-800/50 p-6">
          <h2 class="text-lg font-semibold text-yellow-400 mb-2">Why Most Investors Miss This</h2>
          <p class="text-gray-300">{{ prediction.why_most_miss_it }}</p>
        </div>

        <!-- Full Report -->
        <div class="bg-gray-900 rounded-lg border border-gray-800 p-6">
          <h2 class="text-lg font-semibold text-white mb-3">Full Analysis Report</h2>
          <div class="prose prose-invert prose-sm max-w-none text-gray-300 whitespace-pre-wrap">
            {{ prediction.report_text }}
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-4">
        <!-- Score Card -->
        <div class="bg-gray-900 rounded-lg border border-gray-800 p-4">
          <h3 class="text-sm font-medium text-gray-400 mb-3">Prediction Score</h3>
          <div class="text-4xl font-bold mb-2" :class="prediction.score > 0 ? 'text-green-400' : prediction.score < 0 ? 'text-red-400' : 'text-gray-400'">
            {{ prediction.score > 0 ? '+' : '' }}{{ prediction.score.toFixed(1) }}
          </div>
          <div class="text-sm text-gray-400 mb-3">out of 10</div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-gray-400">Confidence</span>
              <span class="text-white">{{ (prediction.confidence * 100).toFixed(0) }}%</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-gray-400">Timeframe</span>
              <span class="text-white">{{ prediction.timeframe_days }} days</span>
            </div>
            <div v-if="prediction.target_price_low" class="flex justify-between text-sm">
              <span class="text-gray-400">Target Range</span>
              <span class="text-white">
                ${{ prediction.target_price_low.toFixed(2) }} - ${{ prediction.target_price_high?.toFixed(2) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Bull Case -->
        <div class="bg-gray-900 rounded-lg border border-green-800/50 p-4">
          <h3 class="text-sm font-medium text-green-400 mb-2">Bull Case</h3>
          <p class="text-sm text-gray-300 whitespace-pre-wrap">{{ prediction.bull_case }}</p>
        </div>

        <!-- Bear Case -->
        <div class="bg-gray-900 rounded-lg border border-red-800/50 p-4">
          <h3 class="text-sm font-medium text-red-400 mb-2">Bear Case</h3>
          <p class="text-sm text-gray-300 whitespace-pre-wrap">{{ prediction.bear_case }}</p>
        </div>

        <!-- Meta -->
        <div class="bg-gray-900 rounded-lg border border-gray-800 p-4 text-sm text-gray-400">
          <div>Cycle: {{ prediction.cycle_type }}</div>
          <div>Created: {{ new Date(prediction.created_at).toLocaleString() }}</div>
        </div>
      </div>
    </div>
  </div>

  <div v-else class="text-center text-gray-500 py-20">Loading prediction...</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import type { Prediction } from '../types'
import { getPrediction } from '../api/client'
import SignalBadge from '../components/SignalBadge.vue'
import ChainDepthIndicator from '../components/ChainDepthIndicator.vue'

const route = useRoute()
const prediction = ref<Prediction | null>(null)

onMounted(async () => {
  try {
    const id = Number(route.params.id)
    prediction.value = await getPrediction(id)
  } catch (e) {
    console.error('Failed to load prediction:', e)
  }
})
</script>
