<script setup lang="ts">
import { computed } from 'vue'
import { useSessionStore } from '@/stores/session'

const store = useSessionStore()
const label = computed(() => store.locale === 'zh-CN' ? 'EN' : '中')
</script>

<template>
  <button class="language-toggle" type="button" :aria-label="label" @click="store.toggleLocale">
    <span :class="{ active: store.locale === 'zh-CN' }">中</span>
    <span class="divider"></span>
    <span :class="{ active: store.locale === 'en' }">EN</span>
  </button>
</template>

<style scoped>
.language-toggle{height:36px;padding:0 11px;display:flex;align-items:center;gap:8px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft);color:var(--text-faint);font:inherit;font-size:12px;font-weight:700;cursor:pointer}
.language-toggle:hover{border-color:var(--border-bright);background:var(--surface-hover)}
.divider{width:1px;height:12px;background:var(--border-subtle)}
.active{color:var(--cyan-300)}
</style>
