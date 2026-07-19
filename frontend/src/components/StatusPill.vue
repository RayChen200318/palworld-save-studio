<script setup lang="ts">
withDefaults(defineProps<{ tone?: 'cyan' | 'gold' | 'green' | 'red' | 'neutral'; dot?: boolean }>(), { tone: 'neutral', dot: false })
</script>

<template>
  <span class="status-pill" :class="`tone-${tone}`"><i v-if="dot"></i><slot /></span>
</template>

<style scoped>
.status-pill{display:inline-flex;align-items:center;gap:6px;min-height:26px;padding:3px 9px;border:1px solid var(--border-subtle);border-radius:999px;background:var(--surface-soft);color:var(--text-muted);font-size:12px;font-weight:700;letter-spacing:.01em;white-space:nowrap}
.status-pill i{width:6px;height:6px;border-radius:50%;background:currentColor;box-shadow:0 0 8px currentColor}
.tone-cyan{color:var(--cyan-300);border-color:rgba(53,230,209,.26);background:rgba(53,230,209,.09)}
.tone-gold{color:var(--gold-300);border-color:rgba(242,198,109,.25);background:rgba(242,198,109,.09)}
.tone-green{color:var(--green-300);border-color:rgba(85,214,165,.22);background:rgba(85,214,165,.08)}
.tone-red{color:var(--red-300);border-color:rgba(255,122,138,.25);background:rgba(255,122,138,.08)}
</style>
