<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-white">Research Monitor</h1>
      <button
        @click="triggerCycle"
        :disabled="isRunning"
        class="px-4 py-2 rounded-md text-sm font-medium transition"
        :class="isRunning
          ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
          : 'bg-green-600 text-white hover:bg-green-500'"
      >
        {{ isRunning ? 'Cycle Running...' : 'Trigger Research Cycle' }}
      </button>
    </div>

    <!-- Status -->
    <div class="bg-gray-900 rounded-lg border border-gray-800 p-6 mb-6">
      <h2 class="text-lg font-semibold text-white mb-4">System Status</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <div class="text-sm text-gray-400">Scheduler</div>
          <div class="flex items-center mt-1">
            <span
              class="w-2 h-2 rounded-full mr-2"
              :class="health?.scheduler?.running ? 'bg-green-400 animate-pulse' : 'bg-red-400'"
            />
            <span class="text-white">{{ health?.scheduler?.running ? 'Active' : 'Inactive' }}</span>
          </div>
        </div>
        <div>
          <div class="text-sm text-gray-400">Research Cycle</div>
          <div class="flex items-center mt-1">
            <span
              class="w-2 h-2 rounded-full mr-2"
              :class="isRunning ? 'bg-yellow-400 animate-pulse' : 'bg-gray-500'"
            />
            <span class="text-white">{{ isRunning ? 'Running' : 'Idle' }}</span>
          </div>
        </div>
        <div>
          <div class="text-sm text-gray-400">API</div>
          <div class="flex items-center mt-1">
            <span class="w-2 h-2 rounded-full mr-2 bg-green-400" />
            <span class="text-white">v{{ health?.version || '?' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Scheduled Jobs -->
    <div class="bg-gray-900 rounded-lg border border-gray-800 p-6 mb-6">
      <h2 class="text-lg font-semibold text-white mb-4">Scheduled Cycles</h2>
      <div class="space-y-3">
        <div
          v-for="job in health?.scheduler?.jobs || []"
          :key="job.id"
          class="flex items-center justify-between bg-gray-800/50 rounded-md px-4 py-3"
        >
          <div>
            <div class="text-sm text-white font-medium">{{ job.name }}</div>
            <div class="text-xs text-gray-400">{{ job.id }}</div>
          </div>
          <div class="text-sm text-gray-300">
            Next: {{ job.next_run ? new Date(job.next_run).toLocaleString() : 'N/A' }}
          </div>
        </div>
        <div v-if="!health?.scheduler?.jobs?.length" class="text-gray-500 text-sm">
          No scheduled jobs found.
        </div>
      </div>
    </div>

    <!-- Pipeline Overview -->
    <div class="bg-gray-900 rounded-lg border border-gray-800 p-6">
      <h2 class="text-lg font-semibold text-white mb-4">Pipeline Steps</h2>
      <div class="space-y-2">
        <div v-for="step in pipelineSteps" :key="step.name" class="flex items-center gap-3 text-sm">
          <span class="w-6 h-6 rounded-full bg-gray-700 flex items-center justify-center text-xs text-gray-300">
            {{ step.num }}
          </span>
          <span class="text-white font-medium">{{ step.name }}</span>
          <span class="text-gray-500">{{ step.description }}</span>
        </div>
      </div>
    </div>

    <!-- Trigger Result -->
    <div v-if="triggerResult" class="mt-6 bg-gray-900 rounded-lg border border-gray-800 p-4">
      <pre class="text-sm text-green-400">{{ JSON.stringify(triggerResult, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getHealth, getResearchStatus, triggerResearch } from '../api/client'

const health = ref<any>(null)
const isRunning = ref(false)
const triggerResult = ref<any>(null)

const pipelineSteps = [
  { num: 1, name: 'Scrape', description: 'Collect news, Reddit posts, RSS feeds' },
  { num: 2, name: 'Cluster', description: 'Group articles into macro trends using LLM' },
  { num: 3, name: 'Chain Analysis', description: 'Reason through N-order effects per trend' },
  { num: 4, name: 'Validate', description: 'Check discovered tickers: <$10, Robinhood-tradeable' },
  { num: 5, name: 'Graph Update', description: 'Store chain relationships in Neo4j' },
  { num: 6, name: 'Swarm Simulate', description: 'Multi-agent debate on chain validity' },
  { num: 7, name: 'Score & Report', description: 'Generate quantitative prediction + report' },
  { num: 8, name: 'Accuracy Check', description: 'Evaluate predictions from 1-5 days ago' },
]

async function triggerCycle() {
  isRunning.value = true
  triggerResult.value = null
  try {
    triggerResult.value = await triggerResearch('manual')
  } catch (e) {
    console.error('Trigger failed:', e)
    triggerResult.value = { error: 'Failed to trigger cycle' }
  }
}

onMounted(async () => {
  try {
    health.value = await getHealth()
    const status = await getResearchStatus()
    isRunning.value = status.running
  } catch (e) {
    console.error('Failed to load status:', e)
  }
})
</script>
