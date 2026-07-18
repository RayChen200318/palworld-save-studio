<script setup lang="ts">
import AppIcon from './AppIcon.vue'

defineProps<{ title: string; hint?: string; icon?: string }>()
</script>

<template>
  <section class="section-block">
    <header>
      <span v-if="icon"><AppIcon :name="icon" :size="16" /></span>
      <div><h3>{{ title }}</h3><p v-if="hint">{{ hint }}</p></div>
    </header>
    <div class="section-body"><slot /></div>
  </section>
</template>

<style scoped>
.section-block>header{display:flex;align-items:flex-start;gap:9px;margin-bottom:13px}.section-block>header>span{width:28px;height:28px;display:grid;place-items:center;border:1px solid var(--border-subtle);border-radius:8px;background:var(--surface-soft);color:var(--cyan-300)}
h3{margin:1px 0 0;color:var(--text-strong);font-size:12px;font-weight:720}p{margin:4px 0 0;color:var(--text-muted);font-size:8px;line-height:1.5}
</style>
