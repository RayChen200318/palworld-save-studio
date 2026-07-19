<script setup lang="ts">
withDefaults(defineProps<{ compact?: boolean }>(), { compact: false })
const brandLogoUrl = '/brand/palworld-save-studio-logo.svg'
</script>

<template>
  <div class="brand-lockup" :class="{ compact }">
    <img :src="brandLogoUrl" alt="" class="brand-mark" />
    <div class="brand-words">
      <strong>Palworld</strong>
      <span>Save Studio</span>
    </div>
  </div>
</template>

<style scoped>
.brand-lockup{display:flex;align-items:center;gap:12px;color:var(--text-strong)}
.brand-mark{width:46px;height:46px;filter:drop-shadow(0 8px 16px rgba(53,230,209,.14))}
.brand-words{display:flex;flex-direction:column;line-height:1.05;letter-spacing:-.02em}
.brand-words strong{font-size:18px;font-weight:760}
.brand-words span{margin-top:5px;color:var(--text-muted);font-size:12px;font-weight:650;letter-spacing:.08em}
.compact .brand-mark{width:38px;height:38px}.compact .brand-words strong{font-size:16px}.compact .brand-words span{font-size:12px}
</style>
