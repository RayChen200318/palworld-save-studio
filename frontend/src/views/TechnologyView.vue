<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import AppShell from '@/components/AppShell.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import { messages } from '@/i18n/messages'
import { useCatalogStore } from '@/stores/catalog'
import { useCollectionStore } from '@/stores/collection'
import { useDraftStore } from '@/stores/draft'
import { useSessionStore } from '@/stores/session'
import type { TechnologyItem } from '@/types/domain'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const catalog = useCatalogStore()
const collection = useCollectionStore()
const draft = useDraftStore()
const copy = computed(() => messages[session.locale])
const playerId = ref('')
const query = ref('')
const type = ref<'all' | 'normal' | 'boss'>('all')
const unlockOpen = ref(false)
const unlocked = computed(() => new Set(collection.selectedPlayer?.UnlockedRecipeTechnologyNames || []))
const grouped = computed(() => {
  const needle = query.value.trim().toLocaleLowerCase()
  const result = new Map<number, TechnologyItem[]>()
  for (const item of catalog.technologies) {
    if (type.value === 'normal' && item.BossTechnology) continue
    if (type.value === 'boss' && !item.BossTechnology) continue
    if (needle && !`${item.I18n} ${item.InternalName}`.toLocaleLowerCase().includes(needle)) continue
    if (!result.has(item.Level)) result.set(item.Level, [])
    result.get(item.Level)!.push(item)
  }
  return [...result.entries()].sort((a, b) => a[0] - b[0])
})

onMounted(async () => {
  await session.bootstrap()
  if (!session.loaded) {
    router.replace('/')
    return
  }
  await Promise.all([catalog.load(), collection.loadPlayers()])
  playerId.value = typeof route.query.player === 'string' ? route.query.player : collection.players[0]?.PlayerUId || ''
  if (playerId.value) await collection.loadPlayer(playerId.value)
})

async function selectPlayer() {
  if (playerId.value) await collection.loadPlayer(playerId.value)
}

function toggle(item: TechnologyItem) {
  collection.patchTechnology(playerId.value, item.InternalName, !unlocked.value.has(item.InternalName))
}

async function unlockAll() {
  await collection.unlockAllTechnology(playerId.value)
  unlockOpen.value = false
}

function hideBroken(event: Event) {
  ;(event.target as HTMLImageElement).style.display = 'none'
}
</script>

<template>
  <AppShell :eyebrow="copy.technology.eyebrow" :title="copy.technology.title">
    <section class="tech-heading"><p>{{ copy.technology.intro }}</p><button class="button primary" type="button" :disabled="!playerId || draft.pending" @click="unlockOpen = true"><AppIcon name="spark" :size="16" />{{ copy.technology.unlockAll }}</button></section>
    <section class="panel tech-toolbar">
      <label><span>{{ copy.technology.player }}</span><select v-model="playerId" class="field-select" @change="selectPlayer"><option v-for="player in collection.players" :key="player.PlayerUId" :value="player.PlayerUId">{{ player.NickName }}</option></select></label>
      <label class="search"><span>{{ copy.common.search }}</span><div><AppIcon name="search" :size="16" /><input v-model="query" :placeholder="copy.technology.query" /></div></label>
      <div class="type-switch"><button type="button" :class="{ active: type === 'all' }" @click="type = 'all'">{{ copy.common.all }}</button><button type="button" :class="{ active: type === 'normal' }" @click="type = 'normal'">{{ copy.technology.normal }}</button><button type="button" :class="{ active: type === 'boss' }" @click="type = 'boss'">{{ copy.technology.boss }}</button></div>
    </section>

    <div class="technology-scroll">
      <section v-for="[level, items] in grouped" :key="level" class="level-group">
        <header><span>{{ copy.technology.levelGroup }}</span><strong>{{ level }}</strong><i /></header>
        <div class="technology-grid"><button v-for="item in items" :key="item.InternalName" type="button" :class="{ unlocked: unlocked.has(item.InternalName), boss: item.BossTechnology }" :disabled="draft.pending" @click="toggle(item)"><span class="tech-icon"><AppIcon name="book" :size="21" /><img :src="`/image/tech/${item.IconAccessKey}`" alt="" @error="hideBroken" /></span><span class="tech-copy"><strong>{{ item.I18n }}</strong><small>{{ item.InternalName }}</small></span><span class="state">{{ unlocked.has(item.InternalName) ? copy.technology.unlocked : copy.technology.locked }}</span></button></div>
      </section>
      <p v-if="!grouped.length" class="empty">{{ copy.common.noResults }}</p>
    </div>

    <ModalDialog :open="unlockOpen" :title="copy.technology.unlockAllTitle" @close="unlockOpen = false"><p class="dialog-copy">{{ copy.technology.unlockAllCopy }}</p><template #footer><button class="button secondary" type="button" @click="unlockOpen = false">{{ copy.common.cancel }}</button><button class="button primary" type="button" :disabled="draft.pending" @click="unlockAll">{{ copy.technology.unlockAll }}</button></template></ModalDialog>
  </AppShell>
</template>

<style scoped>
.tech-heading{margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;gap:20px}.tech-heading p{max-width:840px;margin:0;color:var(--text-muted);font-size:15px;line-height:1.55}.tech-toolbar{padding:12px;display:grid;grid-template-columns:240px minmax(280px,1fr) auto;align-items:end;gap:12px}.tech-toolbar label>span{display:block;margin-bottom:6px;color:var(--text-faint);font-size:12px;font-weight:700}.search>div{height:40px;padding:0 11px;display:flex;align-items:center;gap:8px;border:1px solid var(--border-subtle);border-radius:9px;background:rgba(5,9,17,.58);color:var(--text-faint)}.search input{width:100%;border:0;outline:0;background:transparent;color:var(--text);font:inherit;font-size:14px}.type-switch{height:40px;padding:3px;display:flex;border:1px solid var(--border-subtle);border-radius:10px;background:rgba(5,9,17,.58)}.type-switch button{padding:0 12px;border:0;border-radius:7px;background:transparent;color:var(--text-muted);font:inherit;font-size:13px;font-weight:700;cursor:pointer}.type-switch button.active{background:linear-gradient(135deg,rgba(53,230,209,.12),rgba(139,124,255,.12));color:var(--cyan-200)}.technology-scroll{height:calc(100vh - 226px);min-height:440px;margin-top:12px;padding-right:5px;overflow:auto}.level-group{margin-bottom:18px}.level-group header{height:30px;display:flex;align-items:center;gap:8px;color:var(--text-faint);font-size:12px;font-weight:700}.level-group header strong{color:var(--violet-200);font-size:16px}.level-group header i{height:1px;flex:1;background:linear-gradient(90deg,var(--border-subtle),transparent)}.technology-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:8px}.technology-grid button{position:relative;min-height:88px;padding:10px 10px 22px;display:grid;grid-template-columns:48px minmax(0,1fr);align-items:center;gap:10px;border:1px solid var(--border-subtle);border-radius:10px;background:linear-gradient(145deg,rgba(20,30,48,.78),rgba(8,11,20,.82));color:var(--text);text-align:left;cursor:pointer}.technology-grid button:hover{border-color:var(--border-bright);transform:translateY(-1px)}.technology-grid button.unlocked{border-color:rgba(85,214,165,.3);background:linear-gradient(145deg,rgba(23,54,49,.7),rgba(10,25,29,.84))}.technology-grid button.boss.unlocked{border-color:rgba(139,124,255,.38);background:linear-gradient(145deg,rgba(41,35,72,.62),rgba(17,20,36,.86))}.tech-icon{position:relative;width:48px;height:48px;display:grid;place-items:center;border-radius:9px;background:rgba(255,255,255,.04);color:var(--text-faint);overflow:hidden}.tech-icon img{position:absolute;inset:2px;width:44px;height:44px;object-fit:contain}.tech-copy{min-width:0}.tech-copy strong,.tech-copy small{display:block;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.tech-copy strong{color:var(--text-strong);font-size:13px}.tech-copy small{margin-top:3px;color:var(--text-faint);font-size:11px}.state{position:absolute;right:8px;bottom:5px;color:var(--text-faint);font-size:12px}.unlocked .state{color:var(--green-300)}.boss.unlocked .state{color:var(--violet-200)}.empty{padding:80px;color:var(--text-muted);font-size:13px;text-align:center}.dialog-copy{margin:0;color:var(--text-muted);font-size:14px;line-height:1.7}
@media(max-width:1366px){.technology-grid{grid-template-columns:repeat(auto-fill,minmax(200px,1fr))}.technology-scroll{height:calc(100vh - 218px)}}
</style>
