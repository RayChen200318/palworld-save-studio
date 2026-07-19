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
.modal-backdrop{position:fixed;inset:0;z-index:100;background:rgba(3,5,10,.78);backdrop-filter:blur(10px);display:grid;place-items:center;padding:24px}
.modal-card{width:100%;max-height:calc(100dvh - 48px);display:grid;grid-template-rows:auto minmax(0,1fr) auto;border:1px solid var(--border-violet);border-radius:14px;background:linear-gradient(150deg,rgba(20,30,48,.97),rgba(8,11,20,.98));box-shadow:var(--shadow-float);overflow:hidden}
header{display:flex;align-items:center;justify-content:space-between;padding:18px 20px;border-bottom:1px solid var(--border-subtle)}
h2{font-size:18px;margin:0;color:var(--text-strong)}
header button{width:34px;height:34px;border:0;border-radius:8px;background:var(--surface-soft);color:var(--text-muted);font-size:22px;line-height:1;cursor:pointer}
header button:hover{background:var(--surface-hover);color:var(--text-strong)}
.modal-body{min-height:0;padding:20px;overflow:auto}.modal-card footer{display:flex;justify-content:flex-end;gap:10px;padding:15px 20px 18px;border-top:1px solid var(--border-subtle)}
.modal-enter-active,.modal-leave-active{transition:opacity .18s ease}.modal-enter-active .modal-card,.modal-leave-active .modal-card{transition:transform .18s ease}
.modal-enter-from,.modal-leave-to{opacity:0}.modal-enter-from .modal-card,.modal-leave-to .modal-card{transform:translateY(8px) scale(.985)}
@media(max-width:720px){.modal-backdrop{padding:16px}.modal-card{max-height:calc(100dvh - 32px)}}
</style>
