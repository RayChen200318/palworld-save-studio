<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import AppShell from '@/components/AppShell.vue'
import StatusPill from '@/components/StatusPill.vue'
import { messages } from '@/i18n/messages'
import { useCatalogStore } from '@/stores/catalog'
import { useCollectionStore } from '@/stores/collection'
import { useSessionStore } from '@/stores/session'

const router = useRouter()
const session = useSessionStore()
const catalog = useCatalogStore()
const collection = useCollectionStore()
const copy = computed(() => messages[session.locale])
const stats = computed(() => session.session.Statistics)
const preview = computed(() => collection.pals.slice(0, 6))
const actions = computed(() => [
  { icon: 'plus', title: copy.value.dashboard.addPal, copy: copy.value.dashboard.addPalHint, to: '/pals?add=1', tone: 'cyan' },
  { icon: 'users', title: copy.value.dashboard.editPlayers, copy: copy.value.dashboard.editPlayersHint, to: '/players', tone: 'gold' },
  { icon: 'book', title: copy.value.dashboard.technology, copy: copy.value.dashboard.technologyHint, to: '/technology', tone: 'cyan' },
  { icon: 'paw', title: copy.value.dashboard.browsePals, copy: copy.value.dashboard.browsePalsHint, to: '/pals', tone: 'gold' },
])

onMounted(async () => {
  await session.bootstrap()
  if (!session.loaded) {
    router.replace('/')
    return
  }
  await Promise.all([catalog.load(), collection.loadPals(), collection.loadPlayers()])
})
</script>

<template>
  <AppShell :eyebrow="copy.dashboard.eyebrow" :title="copy.dashboard.title">
    <section class="dashboard-intro"><div><p>{{ copy.dashboard.intro }}</p><code>{{ session.session.Path }}</code></div><RouterLink to="/pals" class="button primary">{{ copy.dashboard.browsePals }}<AppIcon name="arrow-right" :size="16" /></RouterLink></section>

    <section class="metric-grid">
      <article><span class="metric-icon cyan"><AppIcon name="users" /></span><div><strong>{{ stats.Players }}</strong><p>{{ copy.dashboard.players }}</p></div></article>
      <article><span class="metric-icon cyan"><AppIcon name="paw" /></span><div><strong>{{ stats.Pals }}</strong><p>{{ copy.dashboard.pals }}</p></div></article>
      <article><span class="metric-icon gold"><AppIcon name="briefcase" /></span><div><strong>{{ stats.Humans }}</strong><p>{{ copy.dashboard.humans }}</p></div></article>
      <article><span class="metric-icon red"><AppIcon name="alert" /></span><div><strong>{{ stats.Anomalies }}</strong><p>{{ copy.dashboard.anomalies }}</p></div></article>
    </section>

    <section class="dashboard-grid">
      <article class="panel action-panel">
        <div class="panel-header"><div><h2>{{ copy.dashboard.actionsTitle }}</h2><p>{{ copy.dashboard.path }}</p></div></div>
        <div class="action-grid"><RouterLink v-for="action in actions" :key="action.title" :to="action.to" class="action-card"><span :class="action.tone"><AppIcon :name="action.icon" /></span><div><strong>{{ action.title }}</strong><p>{{ action.copy }}</p></div><AppIcon name="chevron" :size="16" /></RouterLink></div>
      </article>

      <article class="panel anomaly-card">
        <div class="anomaly-icon"><AppIcon name="alert" :size="22" /></div><div><h2>{{ copy.dashboard.issueTitle }}</h2><p>{{ copy.dashboard.issueCopy }}</p><RouterLink to="/pals?anomaly=yes">{{ copy.dashboard.inspect }}<AppIcon name="arrow-right" :size="14" /></RouterLink></div>
      </article>
    </section>

    <section class="panel preview-panel">
      <div class="panel-header"><div><h2>{{ copy.dashboard.recent }}</h2><p>{{ stats.Objects }} {{ copy.pals.total }}</p></div><RouterLink to="/pals">{{ copy.dashboard.viewAll }}<AppIcon name="arrow-right" :size="14" /></RouterLink></div>
      <div v-if="preview.length" class="pal-preview-grid">
        <RouterLink v-for="pal in preview" :key="pal.InstanceId" :to="`/pals/${pal.InstanceId}`" class="pal-preview-card"><img :src="`/image/pals/${pal.IconAccessKey}`" alt="" /><div><strong>{{ pal.SpeciesName }}</strong><span>{{ pal.NickName || pal.CharacterID }}</span><small>{{ copy.common.level }} {{ pal.Level }} · {{ pal.OwnerName || copy.common.none }}</small></div><StatusPill :tone="pal.IsAnomalous ? 'gold' : 'neutral'">{{ copy.locations[pal.Location] }}</StatusPill></RouterLink>
      </div>
      <p v-else class="empty">{{ collection.loading ? copy.common.loading : copy.common.noResults }}</p>
    </section>
  </AppShell>
</template>

<style scoped>
.dashboard-intro{margin-bottom:20px;display:flex;align-items:flex-end;justify-content:space-between;gap:24px}.dashboard-intro p{max-width:780px;margin:0 0 8px;color:var(--text-muted);font-size:13px;line-height:1.7}.dashboard-intro code{color:var(--text-faint);font-size:9px}.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:13px}.metric-grid article{min-height:88px;padding:17px;display:flex;align-items:center;gap:14px;border:1px solid var(--border-subtle);border-radius:14px;background:linear-gradient(145deg,rgba(15,34,52,.8),rgba(8,21,34,.82));box-shadow:var(--shadow-card)}.metric-icon{width:45px;height:45px;display:grid;place-items:center;border-radius:12px}.metric-icon.cyan{background:rgba(34,199,216,.1);color:var(--cyan-300)}.metric-icon.gold{background:rgba(223,185,95,.1);color:var(--gold-300)}.metric-icon.red{background:rgba(217,78,92,.09);color:var(--red-300)}.metric-grid strong{display:block;color:var(--text-strong);font-size:25px;letter-spacing:-.04em}.metric-grid p{margin:3px 0 0;color:var(--text-muted);font-size:10px}
.dashboard-grid{margin-top:15px;display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:15px}.action-grid{padding:14px;display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.action-card{min-height:82px;padding:14px;display:flex;align-items:center;gap:12px;border:1px solid var(--border-subtle);border-radius:12px;background:var(--surface-soft);text-decoration:none}.action-card:hover{border-color:var(--border-bright);background:var(--surface-hover)}.action-card>span{width:38px;height:38px;flex:0 0 38px;display:grid;place-items:center;border-radius:10px}.action-card>span.cyan{color:var(--cyan-300);background:rgba(34,199,216,.1)}.action-card>span.gold{color:var(--gold-300);background:rgba(223,185,95,.1)}.action-card>div{min-width:0;flex:1}.action-card strong{color:var(--text-strong);font-size:12px}.action-card p{margin:5px 0 0;color:var(--text-muted);font-size:9px;line-height:1.45}.action-card>.app-icon{color:var(--text-faint)}
.anomaly-card{padding:20px;display:flex;align-items:flex-start;gap:14px}.anomaly-icon{width:42px;height:42px;flex:0 0 42px;display:grid;place-items:center;border-radius:11px;background:rgba(217,78,92,.09);color:var(--red-300)}.anomaly-card h2{margin:2px 0 7px;color:var(--text-strong);font-size:14px}.anomaly-card p{margin:0;color:var(--text-muted);font-size:10px;line-height:1.65}.anomaly-card a{display:inline-flex;align-items:center;gap:6px;margin-top:14px;color:var(--cyan-300);font-size:10px;font-weight:700;text-decoration:none}
.preview-panel{margin-top:15px}.panel-header a{display:flex;align-items:center;gap:6px;color:var(--cyan-300);font-size:10px;font-weight:700;text-decoration:none}.pal-preview-grid{padding:14px;display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.pal-preview-card{min-width:0;padding:10px;display:flex;align-items:center;gap:10px;border:1px solid var(--border-subtle);border-radius:11px;background:rgba(5,16,27,.35);text-decoration:none}.pal-preview-card:hover{border-color:var(--border-bright)}.pal-preview-card img{width:48px;height:48px;object-fit:contain;border-radius:10px;background:rgba(255,255,255,.035)}.pal-preview-card>div{min-width:0;flex:1}.pal-preview-card strong,.pal-preview-card span,.pal-preview-card small{display:block;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.pal-preview-card strong{color:var(--text-strong);font-size:11px}.pal-preview-card span{margin-top:3px;color:var(--text-muted);font-size:9px}.pal-preview-card small{margin-top:5px;color:var(--text-faint);font-size:8px}.pal-preview-card :deep(.status-pill){font-size:8px}.empty{padding:44px;color:var(--text-muted);font-size:11px;text-align:center}
@media(max-width:1366px){.dashboard-grid{grid-template-columns:minmax(0,1fr) 290px}.pal-preview-grid{grid-template-columns:repeat(2,1fr)}}
</style>
