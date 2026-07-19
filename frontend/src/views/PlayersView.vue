<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import AppShell from '@/components/AppShell.vue'
import StatusPill from '@/components/StatusPill.vue'
import { messages } from '@/i18n/messages'
import { useCollectionStore } from '@/stores/collection'
import { useDraftStore } from '@/stores/draft'
import { useSessionStore } from '@/stores/session'
import type { PlayerDetail } from '@/types/domain'

const router = useRouter()
const session = useSessionStore()
const collection = useCollectionStore()
const draft = useDraftStore()
const copy = computed(() => messages[session.locale])
const form = ref<PlayerDetail | null>(null)

function clone<T>(value: T): T { return JSON.parse(JSON.stringify(value)) as T }

onMounted(async () => {
  await session.bootstrap()
  if (!session.loaded) {
    router.replace('/')
    return
  }
  await collection.loadPlayers()
  if (collection.players[0]) await select(collection.players[0].PlayerUId)
})

async function select(playerId: string) {
  form.value = clone(await collection.loadPlayer(playerId))
}

async function apply(changes: Partial<PlayerDetail>) {
  if (!form.value) return
  form.value = clone(await collection.patchPlayer(form.value.PlayerUId, changes))
}

function textChange(event: Event) { apply({ NickName: (event.target as HTMLInputElement).value }) }
function numberChange(key: 'Level' | 'TechnologyPoint' | 'BossTechnologyPoint', event: Event) { apply({ [key]: Number((event.target as HTMLInputElement).value) }) }
function toggleCage(event: Event) { apply({ HasViewingCage: (event.target as HTMLInputElement).checked }) }
</script>

<template>
  <AppShell :eyebrow="copy.players.eyebrow" :title="copy.players.title">
    <p class="page-intro">{{ copy.players.intro }}</p>
    <section v-if="collection.players.length" class="players-grid">
      <aside class="panel player-list"><div class="panel-header"><div><h2>{{ copy.players.select }}</h2><p>{{ collection.players.length }} {{ copy.dashboard.players }}</p></div></div><button v-for="player in collection.players" :key="player.PlayerUId" type="button" :class="{ active: form?.PlayerUId === player.PlayerUId }" @click="select(player.PlayerUId)"><span class="avatar">{{ player.NickName.slice(0, 2).toUpperCase() }}</span><div><strong>{{ player.NickName }}</strong><small>{{ copy.common.level }} {{ player.Level }} · {{ player.PalCount }} {{ copy.players.palCount }}</small></div><AppIcon name="chevron" :size="15" /></button></aside>

      <article v-if="form" class="panel player-editor">
        <div class="player-hero"><span class="large-avatar">{{ form.NickName.slice(0, 2).toUpperCase() }}</span><div><StatusPill tone="cyan">{{ copy.common.level }} {{ form.Level }}</StatusPill><h2>{{ form.NickName }}</h2><p>{{ form.PlayerUId }}</p></div></div>
        <div class="editor-body">
          <section><h3>{{ copy.pal.identity }}</h3><div class="form-grid"><label><span class="field-label">{{ copy.players.nickname }}</span><input class="field-input" :value="form.NickName" maxlength="64" @blur="textChange" /></label><label><span class="field-label">{{ copy.players.level }}</span><input class="field-input" type="number" min="1" max="80" :value="form.Level" @blur="numberChange('Level', $event)" /></label></div></section>
          <section><h3>{{ copy.players.techPoints }}</h3><div class="form-grid"><label><span class="field-label">{{ copy.players.techPoints }}</span><input class="field-input" type="number" min="0" max="9999" :value="form.TechnologyPoint" @blur="numberChange('TechnologyPoint', $event)" /></label><label><span class="field-label">{{ copy.players.bossPoints }}</span><input class="field-input" type="number" min="0" max="9999" :value="form.BossTechnologyPoint" @blur="numberChange('BossTechnologyPoint', $event)" /></label></div></section>
          <section class="option-row"><div><h3>{{ copy.players.viewingCage }}</h3><p>DisplayCharacter</p></div><label class="switch"><input type="checkbox" :checked="form.HasViewingCage" @change="toggleCage" /><span /></label></section>
          <div class="technology-link"><div><AppIcon name="book" /><span><strong>{{ copy.players.openTech }}</strong><small>{{ form.UnlockedRecipeTechnologyNames.length }} / 588</small></span></div><RouterLink :to="`/technology?player=${form.PlayerUId}`" class="button secondary">{{ copy.common.edit }}<AppIcon name="arrow-right" :size="15" /></RouterLink></div>
          <p v-if="draft.error" class="error">{{ draft.error }}</p>
        </div>
      </article>
    </section>
    <div v-else class="panel empty">{{ copy.players.empty }}</div>
  </AppShell>
</template>

<style scoped>
.page-intro{margin:0 0 16px;color:var(--text-muted);font-size:15px;line-height:1.6}.players-grid{display:grid;grid-template-columns:300px minmax(0,1fr);gap:12px;align-items:start}.player-list{overflow:hidden}.player-list>button{width:100%;min-height:68px;padding:11px 13px;display:flex;align-items:center;gap:11px;border:0;border-bottom:1px solid var(--border-subtle);background:transparent;color:var(--text);text-align:left;cursor:pointer}.player-list>button:hover{background:var(--surface-soft)}.player-list>button.active{background:linear-gradient(90deg,rgba(53,230,209,.1),rgba(139,124,255,.08));box-shadow:inset 3px 0 var(--violet-300)}.player-list .avatar{width:42px;height:42px;flex:0 0 42px;display:grid;place-items:center;border:1px solid var(--border-violet);border-radius:10px;background:linear-gradient(145deg,rgba(53,230,209,.1),rgba(139,124,255,.12));color:var(--cyan-200);font-size:13px;font-weight:800}.player-list button>div{min-width:0;flex:1}.player-list strong,.player-list small{display:block;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.player-list strong{color:var(--text-strong);font-size:15px}.player-list small{margin-top:3px;color:var(--text-muted);font-size:12px}.player-list button>.app-icon{color:var(--text-faint)}.player-editor{overflow:hidden}.player-hero{padding:18px 20px;display:flex;align-items:center;gap:16px;border-bottom:1px solid var(--border-subtle);background:radial-gradient(circle at 10% 50%,rgba(53,230,209,.1),transparent 32%)}.large-avatar{width:72px;height:72px;display:grid;place-items:center;border:1px solid var(--border-violet);border-radius:16px;background:linear-gradient(145deg,rgba(53,230,209,.1),rgba(139,124,255,.14));color:var(--cyan-200);font-size:24px;font-weight:800}.player-hero h2{margin:7px 0 3px;color:var(--text-strong);font-size:22px}.player-hero p{margin:0;color:var(--text-faint);font-size:11px}.player-hero :deep(.status-pill){font-size:12px}.editor-body{padding:20px}.editor-body section+section{margin-top:20px;padding-top:18px;border-top:1px solid var(--border-subtle)}.editor-body h3{margin:0 0 12px;color:var(--text-strong);font-size:16px}.form-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.option-row{display:flex;align-items:center;justify-content:space-between}.option-row h3{margin-bottom:4px}.option-row p{margin:0;color:var(--text-faint);font-size:12px}.switch input{position:absolute;opacity:0}.switch span{width:46px;height:26px;padding:2px;display:block;border:1px solid var(--border-subtle);border-radius:99px;background:#121a2a}.switch span:before{content:"";display:block;width:20px;height:20px;border-radius:50%;background:var(--text-faint);transition:transform 160ms ease,background 160ms ease}.switch input:checked+span{background:rgba(53,230,209,.15);border-color:rgba(53,230,209,.32)}.switch input:checked+span:before{transform:translateX(19px);background:var(--cyan-300)}.technology-link{margin-top:20px;padding:13px 14px;display:flex;align-items:center;justify-content:space-between;border:1px solid var(--border-subtle);border-radius:11px;background:var(--surface-soft)}.technology-link>div{display:flex;align-items:center;gap:11px;color:var(--violet-200)}.technology-link strong,.technology-link small{display:block}.technology-link strong{color:var(--text-strong);font-size:15px}.technology-link small{margin-top:3px;color:var(--text-muted);font-size:12px}.error{color:var(--red-300);font-size:13px}.empty{padding:80px;color:var(--text-muted);font-size:13px;text-align:center}
@media(max-width:1366px){.players-grid{grid-template-columns:270px minmax(0,1fr)}}
</style>
