<script setup lang="ts">
withDefaults(defineProps<{ tone?: 'cyan' | 'gold' | 'green' | 'red' | 'neutral'; dot?: boolean }>(), { tone: 'neutral', dot: false })
</script>

<template>
  <span class="status-pill" :class="`tone-${tone}`"><i v-if="dot"></i><slot /></span>
</template>

<style scoped>
.status-pill{display:inline-flex;align-items:center;gap:7px;min-height:26px;padding:3px 9px;border:1px solid var(--border-subtle);border-radius:999px;background:var(--surface-soft);color:var(--text-muted);font-size:11px;font-weight:700;letter-spacing:.035em;white-space:nowrap}
.status-pill i{width:6px;height:6px;border-radius:50%;background:currentColor;box-shadow:0 0 8px currentColor}
.tone-cyan{color:var(--cyan-300);border-color:rgba(44,210,226,.25);background:rgba(19,168,189,.1)}
.tone-gold{color:var(--gold-300);border-color:rgba(219,181,91,.25);background:rgba(219,181,91,.09)}
.tone-green{color:var(--green-300);border-color:rgba(85,211,157,.22);background:rgba(85,211,157,.08)}
.tone-red{color:var(--red-300);border-color:rgba(241,105,105,.24);background:rgba(241,105,105,.08)}
</style>
