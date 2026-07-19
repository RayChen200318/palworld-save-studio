<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import type { SearchBrowserOption } from '@/types/domain'

const props = defineProps<{
  modelValue: string
  options: SearchBrowserOption[]
  searchPlaceholder: string
  emptyText: string
}>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const query = ref('')
const filtered = computed(() => {
  const needle = query.value.trim().toLocaleLowerCase()
  return needle
    ? props.options.filter((option) => option.searchText.toLocaleLowerCase().includes(needle))
    : props.options
})
const preview = computed(() => props.options.find((option) => option.value === props.modelValue) || filtered.value[0] || null)

watch(() => props.options, (options) => {
  if (props.modelValue && !options.some((option) => option.value === props.modelValue)) emit('update:modelValue', '')
})
</script>

<template>
  <div class="catalog-browser">
    <div class="catalog-browser-left">
      <label class="browser-search"><AppIcon name="search" :size="17" /><input v-model="query" :placeholder="searchPlaceholder" /></label>
      <div class="browser-results">
        <button v-for="option in filtered" :key="option.value" type="button" :class="{ selected: option.value === modelValue }" @click="emit('update:modelValue', option.value)">
          <span><strong>{{ option.title }}</strong><small>{{ option.summary || option.subtitle }}</small></span>
          <span class="browser-meta"><b v-if="option.badge">{{ option.badge }}</b><small v-if="option.meta">{{ option.meta }}</small></span>
        </button>
        <p v-if="!filtered.length">{{ emptyText }}</p>
      </div>
    </div>
    <aside class="browser-preview">
      <slot name="preview" :option="preview">
        <template v-if="preview"><h4>{{ preview.title }}</h4><code>{{ preview.subtitle }}</code><p>{{ preview.summary }}</p></template>
      </slot>
    </aside>
  </div>
</template>

<style scoped>
.catalog-browser{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(230px,.9fr);gap:10px}.catalog-browser-left,.browser-preview{min-width:0;border:1px solid var(--border-subtle);border-radius:10px;background:rgba(5,9,17,.4)}.catalog-browser-left{padding:9px}.browser-search{height:40px;padding:0 10px;display:flex;align-items:center;gap:8px;border:1px solid var(--border-subtle);border-radius:8px;background:#080d17;color:var(--text-faint)}.browser-search input{min-width:0;width:100%;border:0;outline:0;background:transparent;color:var(--text);font:inherit;font-size:14px}.browser-results{height:300px;margin-top:7px;overflow:auto}.browser-results>button{width:100%;min-height:62px;padding:8px 9px;display:flex;align-items:center;justify-content:space-between;gap:10px;border:1px solid transparent;border-radius:8px;background:transparent;color:var(--text);font:inherit;text-align:left;cursor:pointer}.browser-results>button:hover{background:var(--surface-hover)}.browser-results>button.selected{border-color:var(--border-violet);background:var(--surface-selected)}.browser-results button>span:first-child{min-width:0;flex:1}.browser-results strong,.browser-results small{display:block}.browser-results strong{font-size:14px}.browser-results button>span:first-child small{margin-top:4px;overflow:hidden;color:var(--text-muted);font-size:12px;line-height:1.35;text-overflow:ellipsis;white-space:nowrap}.browser-results>p{padding:60px 12px;color:var(--text-muted);font-size:13px;text-align:center}.browser-meta{display:grid;justify-items:end;gap:4px}.browser-meta b{padding:3px 6px;border-radius:5px;background:rgba(139,124,255,.14);color:var(--violet-200);font-size:12px;white-space:nowrap}.browser-meta small{color:var(--gold-300);font-size:12px}.browser-preview{padding:15px}.browser-preview :deep(h4){margin:0;color:var(--text-strong);font-size:16px}.browser-preview :deep(code){display:block;margin-top:5px;overflow-wrap:anywhere;color:var(--text-faint);font-size:11px}.browser-preview :deep(p){margin:13px 0 0;color:var(--text-muted);font-size:13px;line-height:1.65}@media(max-width:850px){.catalog-browser{grid-template-columns:1fr}.browser-preview{min-height:150px}}
</style>
