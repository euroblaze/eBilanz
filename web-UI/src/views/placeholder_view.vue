<script setup lang="ts">
import { useRoute } from 'vue-router'
import BigPrompt from '@/components/ui/big_prompt.vue'
const route = useRoute()
</script>

<template>
  <BigPrompt
    id="placeholder-prompt"
    :titel="(route.meta.titel as string) ?? 'In Vorbereitung'"
    :text="'Diese Ansicht (' + route.path + ') folgt in einem späteren Slice. Siehe ebilanz-ui-prd.md.'"
  />
</template>
