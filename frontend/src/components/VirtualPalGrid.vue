<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import StatusPill from './StatusPill.vue'
import { messages } from '@/i18n/messages'
import { useSessionStore } from '@/stores/session'
import type { PalSummary } from '@/types/domain'
import { computeVirtualWindow } from '@/utils/virtualGrid'

const props = withDefaults(defineProps<{ items: PalSummary[]; rowHeight?: number; overscan?: number }>(), { rowHeight: 202, overscan: 4 })
const session = useSessionStore()
const copy = computed(() => messages[session.locale])
const viewport = ref<HTMLElement | null>(null)
const viewportWidth = ref(900)
const viewportHeight = ref(600)
const scrollTop = ref(0)
let observer: ResizeObserver | null = null
const gap = 10
const columns = computed(() => Math.max(1, Math.floor((viewportWidth.value + gap) / (224 + gap))))
const windowState = computed(() => computeVirtualWindow(props.items.length, columns.value, props.rowHeight, viewportHeight.value, scrollTop.value, props.overscan))
const visibleItems = computed(() => props.items.slice(windowState.value.startIndex, windowState.value.endIndex))

function onScroll(event: Event) {
  scrollTop.value = (event.currentTarget as HTMLElement).scrollTop
}

function stateLabel(flag: string) {
  if (flag === 'outside-container') return copy.value.states.outside
  return copy.value.states[flag as keyof typeof copy.value.states] || flag
}

onMounted(() => {
  if (!viewport.value) return
  const update = () => {
    if (!viewport.value) return
    viewportWidth.value = viewport.value.clientWidth
    viewportHeight.value = viewport.value.clientHeight
  }
  update()
  if (typeof ResizeObserver !== 'undefined') {
    observer = new ResizeObserver(update)
    observer.observe(viewport.value)
  }
})
onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <div ref="viewport" class="virtual-viewport" data-testid="virtual-pal-grid" @scroll="onScroll">
    <div :style="{ height: `${windowState.paddingTop}px` }" />
    <div class="pal-grid" :style="{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }">
      <RouterLink v-for="pal in visibleItems" :key="pal.InstanceId" :to="`/pals/${pal.InstanceId}`" class="pal-card" :style="{ height: `${rowHeight - gap}px` }" :data-instance-id="pal.InstanceId">
        <div class="portrait"><img :src="`/image/pals/${pal.IconAccessKey}`" alt="" /><span v-if="pal.PalDeckId">#{{ pal.PalDeckId }}</span></div>
        <div class="pal-card-body"><h3>{{ pal.SpeciesName }}</h3><p>{{ pal.NickName || pal.CharacterID }}</p><dl><div><dt>{{ copy.common.level }}</dt><dd>{{ pal.Level }}</dd></div><div><dt>{{ copy.common.owner }}</dt><dd>{{ pal.OwnerName || copy.common.none }}</dd></div><div><dt>{{ copy.common.location }}</dt><dd>{{ copy.locations[pal.Location] }}</dd></div></dl></div>
        <div class="card-flags"><StatusPill :tone="pal.ObjectType === 'human' ? 'gold' : 'cyan'">{{ pal.ObjectType === 'human' ? copy.pals.typeHuman : copy.pals.typePal }}</StatusPill><StatusPill v-for="flag in pal.StateFlags.slice(0, 2)" :key="flag" :tone="pal.IsAnomalous ? 'red' : 'gold'">{{ stateLabel(flag) }}</StatusPill></div>
      </RouterLink>
    </div>
    <div :style="{ height: `${windowState.paddingBottom}px` }" />
    <p v-if="!items.length" class="empty">{{ copy.common.noResults }}</p>
  </div>
</template>

<style scoped>
.virtual-viewport{height:calc(100vh - 292px);min-height:430px;overflow:auto;padding-right:4px}.pal-grid{display:grid;gap:10px}.pal-card{position:relative;min-width:0;padding:13px;display:grid;grid-template-columns:78px minmax(0,1fr);grid-template-rows:1fr auto;gap:10px 12px;border:1px solid var(--border-subtle);border-radius:14px;background:linear-gradient(145deg,rgba(16,37,56,.9),rgba(8,21,34,.94));text-decoration:none;overflow:hidden;box-shadow:0 12px 28px rgba(0,0,0,.15)}.pal-card:before{content:"";position:absolute;inset:0 0 auto;height:1px;background:linear-gradient(90deg,transparent,rgba(70,225,236,.3),transparent);opacity:0}.pal-card:hover{border-color:var(--border-bright);transform:translateY(-1px)}.pal-card:hover:before{opacity:1}.portrait{position:relative;width:78px;height:78px;display:grid;place-items:center;border:1px solid rgba(68,206,220,.12);border-radius:13px;background:radial-gradient(circle,rgba(35,190,207,.12),rgba(3,13,22,.4))}.portrait img{width:72px;height:72px;object-fit:contain}.portrait span{position:absolute;left:5px;bottom:4px;padding:2px 5px;border-radius:5px;background:rgba(3,13,22,.82);color:var(--cyan-300);font-size:8px;font-weight:800}.pal-card-body{min-width:0}.pal-card-body h3{margin:3px 0 4px;overflow:hidden;color:var(--text-strong);font-size:13px;white-space:nowrap;text-overflow:ellipsis}.pal-card-body p{margin:0;overflow:hidden;color:var(--text-muted);font-size:9px;white-space:nowrap;text-overflow:ellipsis}.pal-card-body dl{margin:11px 0 0;display:grid;gap:5px}.pal-card-body dl div{min-width:0;display:grid;grid-template-columns:49px 1fr;gap:5px}.pal-card-body dt{color:var(--text-faint);font-size:8px}.pal-card-body dd{margin:0;overflow:hidden;color:var(--text);font-size:8px;white-space:nowrap;text-overflow:ellipsis}.card-flags{grid-column:1/-1;display:flex;align-items:center;gap:5px;overflow:hidden}.card-flags :deep(.status-pill){min-height:21px;padding:2px 7px;font-size:7px}.empty{padding:80px 0;color:var(--text-muted);font-size:12px;text-align:center}
@media(max-height:780px){.virtual-viewport{height:calc(100vh - 270px);min-height:390px}}
</style>
