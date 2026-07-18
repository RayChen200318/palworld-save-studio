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
.brand-mark{width:46px;height:46px;filter:drop-shadow(0 0 14px rgba(41,220,234,.2))}
.brand-words{display:flex;flex-direction:column;line-height:1.05;letter-spacing:-.02em}
.brand-words strong{font-size:17px;font-weight:750}
.brand-words span{font-size:12px;color:var(--text-muted);letter-spacing:.13em;text-transform:uppercase;margin-top:5px}
.compact .brand-mark{width:38px;height:38px}.compact .brand-words strong{font-size:15px}.compact .brand-words span{font-size:10px}
</style>
