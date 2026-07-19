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
  { icon: 'box', title: copy.value.dashboard.items, copy: copy.value.dashboard.itemsHint, to: '/items', tone: 'cyan' },
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
.dashboard-intro{margin-bottom:16px;display:flex;align-items:flex-end;justify-content:space-between;gap:24px}.dashboard-intro p{max-width:820px;margin:0 0 6px;color:var(--text-muted);font-size:15px;line-height:1.55}.dashboard-intro code{display:block;max-width:820px;overflow:hidden;color:var(--text-faint);font-size:11px;white-space:nowrap;text-overflow:ellipsis}.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.metric-grid article{padding:14px 16px;display:flex;align-items:center;gap:14px;border:1px solid var(--border-subtle);border-radius:13px;background:linear-gradient(145deg,rgba(20,30,48,.84),rgba(13,20,34,.72));box-shadow:var(--shadow-card);backdrop-filter:blur(var(--glass-blur))}.metric-icon{width:44px;height:44px;display:grid;place-items:center;border-radius:11px}.metric-icon.cyan{background:rgba(53,230,209,.1);color:var(--cyan-300)}.metric-icon.gold{background:rgba(139,124,255,.12);color:var(--violet-200)}.metric-icon.red{background:rgba(255,122,138,.1);color:var(--red-300)}.metric-grid strong{display:block;color:var(--text-strong);font-size:26px;line-height:1;letter-spacing:-.04em}.metric-grid p{margin:5px 0 0;color:var(--text-muted);font-size:13px}
.dashboard-grid{margin-top:12px;display:grid;grid-template-columns:minmax(0,2.1fr) minmax(270px,.9fr);gap:12px}.action-grid{padding:12px;display:grid;grid-template-columns:repeat(6,1fr);gap:9px}.action-card{grid-column:span 2;min-height:76px;padding:12px 13px;display:flex;align-items:center;gap:11px;border:1px solid var(--border-subtle);border-radius:11px;background:var(--surface-soft);text-decoration:none}.action-card:nth-last-child(2):nth-child(3n+1),.action-card:last-child:nth-child(3n+2){grid-column:span 3}.action-card:hover{border-color:var(--border-bright);background:var(--surface-hover);transform:translateY(-1px)}.action-card>span{width:40px;height:40px;flex:0 0 40px;display:grid;place-items:center;border-radius:10px}.action-card>span.cyan{color:var(--cyan-300);background:rgba(53,230,209,.1)}.action-card>span.gold{color:var(--violet-200);background:rgba(139,124,255,.12)}.action-card>div{min-width:0;flex:1}.action-card strong{color:var(--text-strong);font-size:15px}.action-card p{margin:3px 0 0;color:var(--text-muted);font-size:12px;line-height:1.4}.action-card>.app-icon{color:var(--text-faint)}
.anomaly-card{padding:18px;display:flex;align-items:flex-start;gap:14px}.anomaly-icon{width:44px;height:44px;flex:0 0 44px;display:grid;place-items:center;border-radius:11px;background:rgba(255,122,138,.1);color:var(--red-300)}.anomaly-card h2{margin:1px 0 6px;color:var(--text-strong);font-size:16px}.anomaly-card p{margin:0;color:var(--text-muted);font-size:13px;line-height:1.55}.anomaly-card a{display:inline-flex;align-items:center;gap:6px;margin-top:12px;color:var(--cyan-300);font-size:13px;font-weight:700;text-decoration:none}
.preview-panel{margin-top:12px}.panel-header a{display:flex;align-items:center;gap:6px;color:var(--cyan-300);font-size:13px;font-weight:700;text-decoration:none}.pal-preview-grid{padding:12px;display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.pal-preview-card{min-width:0;padding:10px 11px;display:flex;align-items:center;gap:11px;border:1px solid var(--border-subtle);border-radius:11px;background:rgba(5,9,17,.34);text-decoration:none}.pal-preview-card:hover{border-color:var(--border-bright);background:var(--surface-hover)}.pal-preview-card img{width:50px;height:50px;object-fit:contain;border-radius:10px;background:rgba(255,255,255,.035)}.pal-preview-card>div{min-width:0;flex:1}.pal-preview-card strong,.pal-preview-card span,.pal-preview-card small{display:block;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}.pal-preview-card strong{color:var(--text-strong);font-size:15px}.pal-preview-card span{margin-top:2px;color:var(--text-muted);font-size:13px}.pal-preview-card small{margin-top:3px;color:var(--text-faint);font-size:12px}.pal-preview-card :deep(.status-pill){font-size:12px}.empty{padding:40px;color:var(--text-muted);font-size:13px;text-align:center}
@media(max-width:1366px){.dashboard-grid{grid-template-columns:minmax(0,1fr) 270px}.action-grid{grid-template-columns:repeat(2,1fr)}.action-card,.action-card:nth-last-child(2):nth-child(3n+1),.action-card:last-child:nth-child(3n+2){grid-column:auto}.pal-preview-grid{grid-template-columns:repeat(2,1fr)}.action-card p{display:none}}
</style>
