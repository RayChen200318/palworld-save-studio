<script setup lang="ts">
import { computed } from 'vue'
import AppIcon from '@/components/AppIcon.vue'
import AppShell from '@/components/AppShell.vue'
import StatusPill from '@/components/StatusPill.vue'
import { messages } from '@/i18n/messages'
import { mockPals, mockSave } from '@/mocks/session'
import { usePrototypeStore } from '@/stores/prototype'

const store = usePrototypeStore()
const copy = computed(() => messages[store.locale])
</script>

<template>
  <AppShell :eyebrow="copy.dashboard.eyebrow" :title="mockSave.name[store.locale]">
    <section class="dashboard-intro">
      <div><h2>{{ copy.dashboard.greeting }}</h2><p>{{ copy.dashboard.intro }}</p></div>
      <div class="intro-actions">
        <button class="button secondary disabled-action" type="button" disabled><AppIcon name="users" />{{ copy.dashboard.editPlayers }}</button>
        <RouterLink class="button primary" to="/pals/WorldTreeDragon"><AppIcon name="paw" />{{ copy.dashboard.browsePals }}</RouterLink>
      </div>
    </section>

    <section class="metric-grid">
      <article class="metric-card"><span class="metric-icon cyan"><AppIcon name="users" /></span><div><strong>{{ mockSave.players }}</strong><p>{{ copy.dashboard.players }}</p></div><small>+1</small></article>
      <article class="metric-card"><span class="metric-icon blue"><AppIcon name="paw" /></span><div><strong>{{ mockSave.pals }}</strong><p>{{ copy.dashboard.pals }}</p></div><small>299 {{ store.locale === 'zh-CN' ? '种' : 'species' }}</small></article>
      <article class="metric-card"><span class="metric-icon gold"><AppIcon name="alert" /></span><div><strong>{{ mockSave.warnings }}</strong><p>{{ copy.dashboard.warnings }}</p></div><small>{{ store.locale === 'zh-CN' ? '非阻断' : 'non-blocking' }}</small></article>
      <article class="metric-card"><span class="metric-icon green"><AppIcon name="archive" /></span><div><strong>{{ copy.dashboard.ready }}</strong><p>{{ copy.dashboard.backup }}</p></div><small>{{ store.locale === 'zh-CN' ? '保存时创建' : 'on save' }}</small></article>
    </section>

    <div class="dashboard-grid">
      <div class="dashboard-main">
        <article class="panel health-panel">
          <div class="panel-header">
            <div><h2>{{ copy.dashboard.worldHealth }}</h2><p>{{ copy.dashboard.worldHealthy }}</p></div>
            <StatusPill tone="green" dot>{{ copy.dashboard.verified }}</StatusPill>
          </div>
          <div class="health-list">
            <div><span class="health-icon"><AppIcon name="file" /></span><section><strong>{{ copy.dashboard.levelFile }}</strong><p>42.8 MB · {{ mockSave.updatedAt[store.locale] }}</p></section><StatusPill tone="green"><AppIcon name="check" :size="12" />{{ copy.dashboard.verified }}</StatusPill></div>
            <div><span class="health-icon"><AppIcon name="users" /></span><section><strong>{{ copy.dashboard.playersFolder }}</strong><p>{{ copy.dashboard.found }}</p></section><StatusPill tone="green"><AppIcon name="check" :size="12" />{{ copy.dashboard.verified }}</StatusPill></div>
            <div><span class="health-icon"><AppIcon name="spark" /></span><section><strong>{{ copy.dashboard.versionData }}</strong><p>{{ copy.dashboard.loaded }}</p></section><StatusPill tone="cyan">1.0</StatusPill></div>
          </div>
          <div class="location-bar"><div><span>{{ copy.dashboard.saveLocation }}</span><code>{{ mockSave.path }}</code></div><button type="button"><AppIcon name="external" :size="16" />{{ copy.dashboard.reveal }}</button></div>
        </article>

        <article class="panel recent-panel">
          <div class="panel-header"><div><h2>{{ copy.dashboard.recentPals }}</h2><p>{{ store.locale === 'zh-CN' ? '继续上一次查看的位置' : 'Continue where you left off' }}</p></div><RouterLink to="/pals/WorldTreeDragon">{{ copy.dashboard.viewAll }}<AppIcon name="arrow-right" :size="14" /></RouterLink></div>
          <div class="pal-row">
            <RouterLink v-for="pal in mockPals.slice(0, 4)" :key="pal.id" :to="`/pals/${pal.id}`" class="pal-card">
              <div class="pal-art"><img :src="pal.icon" :alt="pal.name[store.locale]" /><span>Lv. {{ pal.level }}</span></div>
              <div class="pal-card-info"><strong>{{ pal.name[store.locale] }}</strong><p>{{ pal.element[store.locale] }} · {{ pal.owner }}</p></div>
              <AppIcon name="chevron" :size="14" />
            </RouterLink>
          </div>
        </article>
      </div>

      <aside class="dashboard-side">
        <article class="panel quick-panel">
          <div class="panel-header"><h2>{{ copy.dashboard.quickTitle }}</h2></div>
          <button class="quick-action" type="button"><span><AppIcon name="heart" /></span><div><strong>{{ copy.dashboard.heal }}</strong><p>{{ copy.dashboard.healHint }}</p></div><AppIcon name="chevron" :size="15" /></button>
          <button class="quick-action" type="button"><span><AppIcon name="archive" /></span><div><strong>{{ copy.dashboard.backupNow }}</strong><p>{{ copy.dashboard.backupHint }}</p></div><AppIcon name="chevron" :size="15" /></button>
        </article>

        <article class="issue-panel">
          <div class="issue-heading"><span><AppIcon name="alert" /></span><StatusPill tone="gold">INFO</StatusPill></div>
          <h3>{{ copy.dashboard.issueTitle }}</h3><p>{{ copy.dashboard.issueCopy }}</p>
          <button type="button">{{ copy.dashboard.inspect }}<AppIcon name="arrow-right" :size="14" /></button>
        </article>

        <article class="backup-card">
          <div><span>{{ copy.dashboard.backup }}</span><StatusPill tone="green" dot>{{ copy.dashboard.ready }}</StatusPill></div>
          <code>{{ mockSave.backupPath }}</code>
        </article>
      </aside>
    </div>
  </AppShell>
</template>

<style scoped>
.dashboard-intro{display:flex;align-items:center;justify-content:space-between;gap:30px;margin-bottom:20px}.dashboard-intro h2{margin:0;color:var(--text-strong);font-size:24px;letter-spacing:-.025em}.dashboard-intro p{max-width:700px;margin:7px 0 0;color:var(--text-muted);font-size:12px;line-height:1.6}.intro-actions{display:flex;gap:9px}.disabled-action{opacity:.45;cursor:default}.disabled-action:hover{transform:none}
.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}.metric-card{min-height:92px;padding:16px;display:flex;align-items:center;gap:13px;border:1px solid var(--border-subtle);border-radius:14px;background:linear-gradient(145deg,rgba(16,36,54,.88),rgba(9,23,37,.82));box-shadow:0 12px 30px rgba(0,0,0,.12)}.metric-icon{width:42px;height:42px;display:grid;place-items:center;border:1px solid currentColor;border-radius:11px}.metric-icon.cyan{color:var(--cyan-300);background:rgba(41,205,220,.08)}.metric-icon.blue{color:#6eb8f1;background:rgba(84,160,222,.08)}.metric-icon.gold{color:var(--gold-300);background:rgba(219,185,95,.08)}.metric-icon.green{color:var(--green-300);background:rgba(85,211,157,.07)}.metric-card strong{display:block;color:var(--text-strong);font-size:21px;line-height:1}.metric-card p{margin:7px 0 0;color:var(--text-muted);font-size:10px}.metric-card small{margin-left:auto;align-self:flex-end;color:var(--text-faint);font-size:8px;white-space:nowrap}
.dashboard-grid{display:grid;grid-template-columns:minmax(0,1.65fr) minmax(280px,.72fr);gap:16px}.dashboard-main,.dashboard-side{display:flex;flex-direction:column;gap:16px}.health-panel{overflow:hidden}.health-list{padding:4px 20px}.health-list>div{min-height:66px;display:grid;grid-template-columns:36px 1fr auto;align-items:center;gap:12px;border-bottom:1px solid var(--border-subtle)}.health-list>div:last-child{border:0}.health-icon{width:34px;height:34px;display:grid;place-items:center;border-radius:9px;background:var(--surface-soft);color:var(--cyan-300)}.health-list strong{color:var(--text);font-size:11px}.health-list p{margin:4px 0 0;color:var(--text-faint);font-size:9px}.location-bar{margin:2px 20px 18px;padding:11px 12px;display:flex;align-items:center;justify-content:space-between;gap:20px;border:1px solid var(--border-subtle);border-radius:10px;background:rgba(3,12,21,.45)}.location-bar>div{min-width:0}.location-bar span{display:block;margin-bottom:5px;color:var(--text-faint);font-size:8px;text-transform:uppercase;letter-spacing:.08em}.location-bar code{display:block;overflow:hidden;color:#99b2bd;font-size:8px;white-space:nowrap;text-overflow:ellipsis}.location-bar button{display:flex;align-items:center;gap:7px;flex-shrink:0;border:0;background:transparent;color:var(--cyan-300);font-size:9px;cursor:pointer}
.recent-panel{overflow:hidden}.recent-panel .panel-header a{display:flex;align-items:center;gap:6px;color:var(--cyan-300);font-size:10px;text-decoration:none}.pal-row{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;padding:14px}.pal-card{min-width:0;padding:8px;border:1px solid var(--border-subtle);border-radius:11px;background:rgba(5,17,28,.45);text-decoration:none;transition:.17s ease}.pal-card:hover{transform:translateY(-2px);border-color:var(--border-bright);background:var(--surface-hover)}.pal-art{position:relative;height:76px;display:grid;place-items:center;border-radius:8px;background:radial-gradient(circle at 50% 35%,rgba(65,208,222,.15),rgba(8,24,37,.75));overflow:hidden}.pal-art img{width:72px;height:72px;object-fit:contain;filter:drop-shadow(0 6px 9px rgba(0,0,0,.42))}.pal-art span{position:absolute;right:5px;bottom:5px;padding:2px 5px;border-radius:5px;background:rgba(3,11,18,.82);color:var(--gold-200);font-size:8px;font-weight:700}.pal-card-info{min-width:0;margin-top:8px}.pal-card-info strong{display:block;overflow:hidden;color:var(--text-strong);font-size:10px;white-space:nowrap;text-overflow:ellipsis}.pal-card-info p{margin:4px 0 0;overflow:hidden;color:var(--text-faint);font-size:8px;white-space:nowrap;text-overflow:ellipsis}.pal-card>.app-icon{display:none}
.quick-panel{overflow:hidden}.quick-panel .panel-header{padding-top:16px;padding-bottom:14px}.quick-action{width:100%;min-height:75px;padding:13px 16px;display:grid;grid-template-columns:36px 1fr auto;align-items:center;gap:11px;border:0;border-bottom:1px solid var(--border-subtle);background:transparent;color:var(--text);text-align:left;cursor:pointer}.quick-action:last-child{border-bottom:0}.quick-action:hover{background:var(--surface-hover)}.quick-action>span{width:34px;height:34px;display:grid;place-items:center;border-radius:9px;background:rgba(39,202,217,.08);color:var(--cyan-300)}.quick-action strong{font-size:10px}.quick-action p{margin:4px 0 0;color:var(--text-faint);font-size:8px;line-height:1.5}.quick-action>.app-icon{color:var(--text-faint)}
.issue-panel{padding:17px;border:1px solid rgba(222,184,94,.2);border-radius:14px;background:linear-gradient(145deg,rgba(87,68,29,.22),rgba(34,28,18,.34))}.issue-heading{display:flex;align-items:center;justify-content:space-between}.issue-heading>span{width:34px;height:34px;display:grid;place-items:center;border-radius:9px;background:rgba(219,185,95,.1);color:var(--gold-300)}.issue-panel h3{margin:15px 0 7px;color:var(--gold-100);font-size:12px}.issue-panel p{margin:0;color:#a99d81;font-size:9px;line-height:1.65}.issue-panel button{margin-top:13px;padding:0;display:flex;align-items:center;gap:6px;border:0;background:transparent;color:var(--gold-300);font-size:9px;font-weight:700;cursor:pointer}.backup-card{padding:15px;border:1px solid var(--border-subtle);border-radius:13px;background:var(--surface-soft)}.backup-card>div{display:flex;align-items:center;justify-content:space-between;color:var(--text-muted);font-size:9px}.backup-card code{display:block;margin-top:12px;overflow:hidden;color:var(--text-faint);font-size:8px;white-space:nowrap;text-overflow:ellipsis}
@media(max-width:1366px){.metric-card{padding:13px}.metric-icon{width:38px;height:38px}.metric-card strong{font-size:18px}.dashboard-grid{grid-template-columns:minmax(0,1.55fr) minmax(260px,.7fr)}.pal-art{height:66px}.pal-art img{width:64px;height:64px}.dashboard-intro h2{font-size:21px}}
@media(max-height:760px){.dashboard-intro{margin-bottom:14px}.metric-grid{margin-bottom:13px}.metric-card{min-height:76px}.page-content{padding-top:18px}.health-list>div{min-height:58px}.location-bar{margin-bottom:14px}.quick-action{min-height:66px}.issue-panel{padding:14px}.recent-panel{display:none}}
</style>
