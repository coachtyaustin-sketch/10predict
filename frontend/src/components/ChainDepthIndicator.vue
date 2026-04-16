<template>
  <div class="flex items-center gap-1" :title="`${depth}-order effect (deeper = more hidden)`">
    <span
      v-for="n in maxDepth"
      :key="n"
      class="w-2 h-2 rounded-full"
      :class="n <= depth ? 'bg-purple-400' : 'bg-gray-700'"
    />
    <span class="text-xs text-purple-400 ml-1">{{ depthLabel }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ depth: number }>()
const maxDepth = 5

const depthLabel = computed(() => {
  if (props.depth <= 1) return '1st order'
  if (props.depth === 2) return '2nd order'
  if (props.depth === 3) return '3rd order'
  return `${props.depth}th order`
})
</script>
