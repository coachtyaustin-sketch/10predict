<template>
  <div class="flex items-center gap-2">
    <div class="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
      <div
        class="h-full rounded-full transition-all duration-300"
        :class="barColor"
        :style="{ width: `${confidence * 100}%` }"
      />
    </div>
    <span class="text-xs text-gray-400">{{ (confidence * 100).toFixed(0) }}%</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ confidence: number }>()

const barColor = computed(() => {
  if (props.confidence >= 0.7) return 'bg-green-500'
  if (props.confidence >= 0.4) return 'bg-yellow-500'
  return 'bg-red-500'
})
</script>
