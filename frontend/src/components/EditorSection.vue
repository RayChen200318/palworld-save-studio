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
.section-block>header{display:flex;align-items:flex-start;gap:10px;margin-bottom:14px}.section-block>header>span{width:32px;height:32px;display:grid;place-items:center;border:1px solid var(--border-subtle);border-radius:9px;background:linear-gradient(145deg,rgba(53,230,209,.08),rgba(139,124,255,.08));color:var(--cyan-300)}
h3{margin:1px 0 0;color:var(--text-strong);font-size:16px;font-weight:720}p{margin:3px 0 0;color:var(--text-muted);font-size:13px;line-height:1.5}
</style>
