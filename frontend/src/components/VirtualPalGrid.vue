<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import StatusPill from './StatusPill.vue'
import { messages } from '@/i18n/messages'
import { useSessionStore } from '@/stores/session'
import type { PalSummary } from '@/types/domain'
import { computeVirtualWindow } from '@/utils/virtualGrid'

const props = withDefaults(defineProps<{ items: PalSummary[]; rowHeight?: number; overscan?: number }>(), { rowHeight: 218, overscan: 4 })
const session = useSessionStore()
const copy = computed(() => messages[session.locale])
const viewport = ref<HTMLElement | null>(null)
const viewportWidth = ref(900)
const viewportHeight = ref(600)
const scrollTop = ref(0)
let observer: ResizeObserver | null = null
const gap = 10
const columns = computed(() => Math.max(1, Math.floor((viewportWidth.value + gap) / (248 + gap))))
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
.virtual-viewport{height:calc(100vh - 252px);min-height:420px;overflow:auto;padding-right:4px}.pal-grid{display:grid;gap:10px}.pal-card{position:relative;min-width:0;padding:14px;display:grid;grid-template-columns:82px minmax(0,1fr);grid-template-rows:1fr auto;gap:11px 13px;border:1px solid var(--border-subtle);border-radius:13px;background:linear-gradient(145deg,rgba(20,30,48,.86),rgba(8,11,20,.9));text-decoration:none;overflow:hidden;box-shadow:0 12px 28px rgba(0,0,0,.17)}.pal-card:before{content:"";position:absolute;inset:0 0 auto;height:2px;background:linear-gradient(90deg,transparent,var(--cyan-300),var(--violet-300),transparent);opacity:0}.pal-card:hover{border-color:var(--border-violet);transform:translateY(-1px);background:linear-gradient(145deg,rgba(24,36,56,.9),rgba(11,16,29,.94))}.pal-card:hover:before{opacity:1}.portrait{position:relative;width:82px;height:82px;display:grid;place-items:center;border:1px solid var(--border-subtle);border-radius:12px;background:radial-gradient(circle,rgba(53,230,209,.11),rgba(5,9,17,.45))}.portrait img{width:76px;height:76px;object-fit:contain}.portrait span{position:absolute;left:5px;bottom:4px;padding:2px 5px;border-radius:5px;background:rgba(5,9,17,.88);color:var(--cyan-300);font-size:12px;font-weight:800}.pal-card-body{min-width:0}.pal-card-body h3{margin:2px 0 3px;overflow:hidden;color:var(--text-strong);font-size:16px;white-space:nowrap;text-overflow:ellipsis}.pal-card-body p{margin:0;overflow:hidden;color:var(--text-muted);font-size:13px;white-space:nowrap;text-overflow:ellipsis}.pal-card-body dl{margin:10px 0 0;display:grid;gap:4px}.pal-card-body dl div{min-width:0;display:grid;grid-template-columns:58px 1fr;gap:5px}.pal-card-body dt{color:var(--text-faint);font-size:12px}.pal-card-body dd{margin:0;overflow:hidden;color:var(--text);font-size:12px;white-space:nowrap;text-overflow:ellipsis}.card-flags{grid-column:1/-1;display:flex;align-items:center;gap:5px;overflow:hidden}.card-flags :deep(.status-pill){min-height:24px;padding:2px 7px;font-size:12px}.empty{padding:80px 0;color:var(--text-muted);font-size:13px;text-align:center}
@media(max-height:780px){.virtual-viewport{height:calc(100vh - 236px);min-height:380px}}
</style>
