<template>
  <span
    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold"
    :class="badgeClass"
  >
    {{ label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SignalType } from '../types'
import { SIGNAL_LABELS } from '../types'

const props = defineProps<{ signal: string }>()

const label = computed(() => SIGNAL_LABELS[props.signal as SignalType] || props.signal)

const badgeClass = computed(() => {
  switch (props.signal) {
    case 'STRONG_BUY': return 'bg-green-600 text-white'
    case 'BUY': return 'bg-green-500/20 text-green-400 border border-green-500/40'
    case 'HOLD': return 'bg-gray-600/20 text-gray-400 border border-gray-500/40'
    case 'SELL': return 'bg-red-500/20 text-red-400 border border-red-500/40'
    case 'STRONG_SELL': return 'bg-red-600 text-white'
    default: return 'bg-gray-600 text-gray-300'
  }
})
</script>
