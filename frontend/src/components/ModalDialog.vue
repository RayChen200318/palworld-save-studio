<script setup lang="ts">
defineProps<{ open: boolean; title: string; width?: string }>()
defineEmits<{ close: [] }>()
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal-backdrop" @click.self="$emit('close')">
        <section class="modal-card" role="dialog" aria-modal="true" :aria-label="title" :style="{ maxWidth: width || '540px' }">
          <header><h2>{{ title }}</h2><button type="button" aria-label="Close" @click="$emit('close')">×</button></header>
          <div class="modal-body"><slot /></div>
          <footer v-if="$slots.footer"><slot name="footer" /></footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-backdrop{position:fixed;inset:0;z-index:100;background:rgba(1,7,13,.76);backdrop-filter:blur(8px);display:grid;place-items:center;padding:24px}
.modal-card{width:100%;border:1px solid var(--border-bright);border-radius:18px;background:linear-gradient(150deg,rgba(18,35,54,.98),rgba(8,19,32,.99));box-shadow:0 28px 80px rgba(0,0,0,.55),0 0 40px rgba(31,207,224,.06);overflow:hidden}
header{display:flex;align-items:center;justify-content:space-between;padding:20px 22px;border-bottom:1px solid var(--border-subtle)}
h2{font-size:18px;margin:0;color:var(--text-strong)}
header button{width:32px;height:32px;border:0;border-radius:8px;background:var(--surface-soft);color:var(--text-muted);font-size:22px;line-height:1;cursor:pointer}
.modal-body{padding:22px}.modal-card footer{display:flex;justify-content:flex-end;gap:10px;padding:16px 22px 20px;border-top:1px solid var(--border-subtle)}
.modal-enter-active,.modal-leave-active{transition:opacity .18s ease}.modal-enter-active .modal-card,.modal-leave-active .modal-card{transition:transform .18s ease}
.modal-enter-from,.modal-leave-to{opacity:0}.modal-enter-from .modal-card,.modal-leave-to .modal-card{transform:translateY(8px) scale(.985)}
</style>
