<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import type { SearchSelectOption } from '@/types/domain'

const props = defineProps<{
  modelValue: string
  options: SearchSelectOption[]
  placeholder: string
  searchPlaceholder: string
  emptyText: string
  disabled?: boolean
  mode?: 'popover' | 'inline-grid'
}>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
  close: []
}>()

const root = ref<HTMLElement | null>(null)
const input = ref<HTMLInputElement | null>(null)
const open = ref(false)
const query = ref('')
const activeIndex = ref(0)
const compact = ref(false)
let compactQuery: MediaQueryList | null = null
const selected = computed(() => props.options.find((option) => option.value === props.modelValue))
const filtered = computed(() => {
  const needle = query.value.trim().toLocaleLowerCase()
  if (!needle) return props.options
  return props.options.filter((option) => option.searchText.toLocaleLowerCase().includes(needle))
})

watch([query, () => props.options], () => { activeIndex.value = 0 })

async function show() {
  if (props.disabled) return
  open.value = true
  query.value = ''
  const selectedIndex = props.options.findIndex((option) => option.value === props.modelValue)
  activeIndex.value = Math.max(0, selectedIndex)
  await nextTick()
  input.value?.focus()
}

function close() {
  if (!open.value) return
  open.value = false
  emit('close')
}

function choose(option: SearchSelectOption) {
  emit('update:modelValue', option.value)
  close()
}

function move(delta: number) {
  if (!filtered.value.length) return
  activeIndex.value = (activeIndex.value + delta + filtered.value.length) % filtered.value.length
  nextTick(() => {
    const active = root.value?.querySelector<HTMLElement>('[data-active="true"]')
    if (active && typeof active.scrollIntoView === 'function') active.scrollIntoView({ block: 'nearest' })
  })
}

function onKeydown(event: KeyboardEvent) {
  const columns = props.mode === 'inline-grid' && !compact.value ? 2 : 1
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    move(columns)
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    move(-columns)
  } else if (event.key === 'ArrowRight' && columns > 1) {
    event.preventDefault()
    move(1)
  } else if (event.key === 'ArrowLeft' && columns > 1) {
    event.preventDefault()
    move(-1)
  } else if (event.key === 'Enter' && filtered.value[activeIndex.value]) {
    event.preventDefault()
    choose(filtered.value[activeIndex.value])
  } else if (event.key === 'Escape') {
    event.preventDefault()
    close()
  }
}

function outside(event: MouseEvent) {
  if (root.value && !root.value.contains(event.target as Node)) close()
}

function updateCompact() {
  compact.value = compactQuery?.matches || false
}

onMounted(() => {
  document.addEventListener('mousedown', outside)
  if (typeof window.matchMedia === 'function') {
    compactQuery = window.matchMedia('(max-width: 720px)')
    updateCompact()
    compactQuery.addEventListener('change', updateCompact)
  }
})
onBeforeUnmount(() => {
  document.removeEventListener('mousedown', outside)
  compactQuery?.removeEventListener('change', updateCompact)
})
</script>

<template>
  <div ref="root" class="searchable-select" :class="[{ open, disabled }, mode === 'inline-grid' ? 'inline-grid' : 'popover-mode']">
    <button class="select-trigger" type="button" :disabled="disabled" :aria-expanded="open" @click="open ? close() : show()" @keydown.down.prevent="show">
      <img v-if="selected?.iconUrl" :src="selected.iconUrl" alt="" />
      <span class="trigger-copy">
        <strong>{{ selected?.title || placeholder }}</strong>
        <small v-if="selected">{{ selected.subtitle }}<template v-if="selected.meta"> · {{ selected.meta }}</template></small>
      </span>
      <span v-if="selected?.badge" class="option-badge">{{ selected.badge }}</span>
      <AppIcon name="chevron" :size="15" />
    </button>
    <div v-if="open" class="select-popover" @keydown="onKeydown">
      <label class="select-search"><AppIcon name="search" :size="17" /><input ref="input" v-model="query" :placeholder="searchPlaceholder" /></label>
      <div class="select-results" role="listbox">
        <button
          v-for="(option, index) in filtered"
          :key="option.value"
          type="button"
          role="option"
          :aria-selected="option.value === modelValue"
          :class="{ active: index === activeIndex, selected: option.value === modelValue }"
          :data-active="index === activeIndex"
          @mouseenter="activeIndex = index"
          @click="choose(option)"
        >
          <img v-if="option.iconUrl" :src="option.iconUrl" alt="" loading="lazy" />
          <span><strong>{{ option.title }}</strong><small>{{ option.subtitle }}</small></span>
          <span class="option-meta"><b v-if="option.badge">{{ option.badge }}</b><small v-if="option.meta">{{ option.meta }}</small></span>
        </button>
        <p v-if="!filtered.length" class="select-empty">{{ emptyText }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.searchable-select{position:relative;min-width:0}.select-trigger{width:100%;min-height:44px;padding:5px 10px;display:flex;align-items:center;gap:9px;border:1px solid var(--border-subtle);border-radius:9px;background:rgba(5,9,17,.58);color:var(--text);font:inherit;text-align:left;cursor:pointer}.select-trigger:hover,.searchable-select.open .select-trigger{border-color:var(--violet-300)}.select-trigger:focus-visible{outline:2px solid var(--cyan-300);outline-offset:2px}.select-trigger>img{width:34px;height:34px;flex:0 0 34px;object-fit:contain}.trigger-copy{min-width:0;flex:1}.trigger-copy strong,.trigger-copy small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.trigger-copy strong{font-size:14px}.trigger-copy small{margin-top:2px;color:var(--text-faint);font-size:12px}.select-trigger>.app-icon{transform:rotate(90deg);color:var(--text-faint)}.option-badge,.option-meta b{padding:3px 6px;border-radius:5px;background:rgba(139,124,255,.14);color:var(--violet-200);font-size:12px;font-weight:750;white-space:nowrap}.select-popover{position:absolute;z-index:90;top:calc(100% + 6px);left:0;width:max(100%,410px);padding:8px;border:1px solid var(--border-violet);border-radius:11px;background:rgba(13,20,34,.98);box-shadow:var(--shadow-float)}.inline-grid .select-popover{position:relative;top:auto;left:auto;width:100%;margin-top:8px;box-shadow:none}.select-search{height:40px;padding:0 10px;display:flex;align-items:center;gap:8px;border:1px solid var(--border-subtle);border-radius:8px;background:#080d17;color:var(--text-faint)}.select-search input{width:100%;border:0;outline:0;background:transparent;color:var(--text);font:inherit;font-size:14px}.select-results{max-height:310px;margin-top:7px;overflow:auto}.inline-grid .select-results{max-height:350px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));align-content:start;gap:4px}.select-results>button{width:100%;min-width:0;min-height:58px;padding:7px 8px;display:flex;align-items:center;gap:9px;border:1px solid transparent;border-radius:8px;background:transparent;color:var(--text);font:inherit;text-align:left;cursor:pointer}.select-results>button:hover,.select-results>button.active{background:var(--surface-hover);border-color:var(--border-subtle)}.select-results>button.selected{border-color:rgba(53,230,209,.25);background:rgba(53,230,209,.07)}.select-results img{width:42px;height:42px;flex:0 0 42px;object-fit:contain}.select-results button>span:nth-child(2){min-width:0;flex:1}.select-results strong,.select-results small{display:block}.select-results strong{overflow:hidden;font-size:14px;text-overflow:ellipsis;white-space:nowrap}.select-results button>span:nth-child(2) small{margin-top:3px;overflow:hidden;color:var(--text-faint);font-size:11px;text-overflow:ellipsis;white-space:nowrap}.option-meta{display:grid;justify-items:end;gap:4px}.option-meta small{color:var(--cyan-300);font-size:12px}.select-empty{margin:0;padding:38px 12px;color:var(--text-muted);font-size:13px;text-align:center}.inline-grid .select-empty{grid-column:1/-1}.disabled{opacity:.55}@media(max-width:720px){.select-popover{width:100%}.inline-grid .select-results{grid-template-columns:1fr}}
</style>
