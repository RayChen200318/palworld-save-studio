<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from './AppIcon.vue'
import BrandLockup from './BrandLockup.vue'
import LanguageToggle from './LanguageToggle.vue'
import ModalDialog from './ModalDialog.vue'
import StatusPill from './StatusPill.vue'
import { messages } from '@/i18n/messages'
import { apiClient } from '@/services/apiClient'
import { useCollectionStore } from '@/stores/collection'
import { useDraftStore } from '@/stores/draft'
import { useSessionStore } from '@/stores/session'

defineProps<{ eyebrow: string; title: string }>()

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const draft = useDraftStore()
const collection = useCollectionStore()
const copy = computed(() => messages[session.locale])
const settingsOpen = ref(false)
const disableBackupOpen = ref(false)
const saveOpen = ref(false)
const changeOpen = ref(false)
const updateState = ref<'idle' | 'checking' | 'current' | 'available' | 'none' | 'failed'>('idle')
const latestVersion = ref('')
const active = computed(() => String(route.name || '').split('-')[0])
const searchVisible = computed(() => active.value === 'pals')
const updateLabel = computed(() => {
  if (updateState.value === 'checking') return copy.value.settings.checking
  if (updateState.value === 'current') return copy.value.settings.current
  if (updateState.value === 'available') return `${copy.value.settings.available} ${latestVersion.value}`
  if (updateState.value === 'none') return copy.value.settings.noRelease
  if (updateState.value === 'failed') return copy.value.settings.updateFailed
  return copy.value.settings.check
})

function requestChangeSave() {
  if (session.dirty) changeOpen.value = true
  else router.push('/')
}

async function discardAndChange() {
  await session.discardDraft()
  collection.clear()
  changeOpen.value = false
  router.push('/')
}

async function commit() {
  if (!draft.canCommit) return
  await session.commitDraft()
  saveOpen.value = false
  await Promise.all([collection.loadPals(true), collection.loadPlayers(true)])
}

async function toggleBackup() {
  if (session.session.BackupEnabled) disableBackupOpen.value = true
  else await session.setBackupEnabled(true)
}

async function disableBackup() {
  await session.setBackupEnabled(false)
  disableBackupOpen.value = false
}

async function checkUpdate() {
  updateState.value = 'checking'
  try {
    const result = await apiClient.getUpdateStatus()
    latestVersion.value = result.LatestVersion || ''
    updateState.value = !result.LatestVersion
      ? 'none'
      : result.UpdateAvailable ? 'available' : 'current'
  } catch {
    updateState.value = 'failed'
  }
}
</script>

<template>
  <div class="app-frame">
    <aside class="sidebar">
      <BrandLockup />
      <nav class="main-nav" :aria-label="copy.nav.overview">
        <span class="nav-label">{{ copy.nav.overview }}</span>
        <RouterLink to="/dashboard" class="nav-item" :class="{ active: active === 'dashboard' }"><AppIcon name="grid" /><span>{{ copy.nav.dashboard }}</span></RouterLink>
        <RouterLink to="/pals" class="nav-item" :class="{ active: active === 'pals' || active === 'pal' }"><AppIcon name="paw" /><span>{{ copy.nav.pals }}</span></RouterLink>
        <RouterLink to="/players" class="nav-item" :class="{ active: active === 'players' }"><AppIcon name="users" /><span>{{ copy.nav.players }}</span></RouterLink>
        <RouterLink to="/technology" class="nav-item" :class="{ active: active === 'technology' }"><AppIcon name="book" /><span>{{ copy.nav.technology }}</span></RouterLink>
      </nav>

      <div class="world-card">
        <div class="world-heading"><span>{{ copy.nav.loadedWorld }}</span><StatusPill tone="green" dot>LIVE</StatusPill></div>
        <strong>{{ session.worldName || copy.nav.noWorld }}</strong>
        <div class="world-source"><AppIcon name="server" :size="15" />Palworld 1.0</div>
        <button class="change-save" type="button" @click="requestChangeSave">{{ copy.nav.changeSave }}<AppIcon name="chevron" :size="14" /></button>
      </div>

      <div class="sidebar-bottom">
        <button class="nav-item settings-button" type="button" @click="settingsOpen = true"><AppIcon name="settings" /><span>{{ copy.nav.settings }}</span></button>
        <div class="build-info"><span>{{ copy.common.version }}</span><span>{{ copy.common.unofficial }}</span></div>
      </div>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <div class="page-heading"><span>{{ eyebrow }}</span><h1>{{ title }}</h1></div>
        <div class="topbar-actions">
          <label v-if="searchVisible" class="search-box"><AppIcon name="search" :size="18" /><input v-model="collection.filters.query" :placeholder="copy.pals.query" /></label>
          <StatusPill v-if="draft.pending" tone="gold" dot>{{ copy.common.pending }}</StatusPill>
          <StatusPill v-else-if="session.dirty" tone="gold" dot>{{ copy.common.unsaved }}</StatusPill>
          <button class="button primary save-button" type="button" :disabled="!draft.canCommit || session.busy" @click="saveOpen = true"><AppIcon name="save" :size="16" />{{ session.busy ? copy.common.saving : copy.common.save }}</button>
          <LanguageToggle />
          <div class="avatar">RC</div>
        </div>
      </header>
      <main class="page-content"><slot /></main>
    </div>

    <ModalDialog :open="saveOpen" :title="copy.dialogs.saveTitle" @close="saveOpen = false">
      <div class="path-confirm"><span>{{ copy.dialogs.target }}</span><code>{{ session.session.Path }}</code></div>
      <p v-if="session.error" class="error-copy">{{ session.error }}</p>
      <template #footer><button class="button secondary" type="button" @click="saveOpen = false">{{ copy.common.cancel }}</button><button class="button primary" type="button" :disabled="draft.pending || session.busy" @click="commit">{{ copy.common.save }}</button></template>
    </ModalDialog>

    <ModalDialog :open="changeOpen" :title="copy.dialogs.changeTitle" @close="changeOpen = false">
      <p class="dialog-copy">{{ copy.dialogs.changeCopy }}</p>
      <template #footer><button class="button secondary" type="button" @click="changeOpen = false">{{ copy.common.cancel }}</button><button class="button danger" type="button" @click="discardAndChange">{{ copy.dialogs.discard }}</button></template>
    </ModalDialog>

    <ModalDialog :open="settingsOpen" :title="copy.settings.title" width="620px" @close="settingsOpen = false">
      <div class="about-hero"><img src="/brand/palworld-save-studio-logo.svg" alt="" /><div><strong>Palworld Save Studio</strong><StatusPill tone="cyan">{{ copy.common.beta }}</StatusPill></div></div>
      <div class="setting-row"><div><strong>{{ copy.settings.language }}</strong><p>简体中文 / English</p></div><LanguageToggle /></div>
      <div class="setting-row"><div><strong>{{ copy.settings.backup }}</strong><p>{{ copy.settings.backupHint }}</p></div><button class="toggle" :class="{ enabled: session.session.BackupEnabled }" type="button" :aria-pressed="session.session.BackupEnabled" @click="toggleBackup"><span /></button></div>
      <div class="setting-row"><div><strong>{{ copy.settings.update }}</strong><p>{{ copy.settings.updateHint }}</p></div><button class="button secondary compact-button" type="button" :disabled="updateState === 'checking'" @click="checkUpdate">{{ updateLabel }}</button></div>
      <div class="legal-block"><div><span>{{ copy.settings.maintainer }}</span><strong>{{ copy.settings.maintainerName }}</strong></div><h3>{{ copy.settings.license }}</h3><p>{{ copy.settings.legal }}</p><p>{{ copy.settings.disclaimer }}</p></div>
      <template #footer><button class="button primary" type="button" @click="settingsOpen = false">{{ copy.common.close }}</button></template>
    </ModalDialog>

    <ModalDialog :open="disableBackupOpen" :title="copy.settings.disableBackup" @close="disableBackupOpen = false">
      <p class="dialog-copy">{{ copy.settings.disableBackupCopy }}</p>
      <template #footer><button class="button secondary" type="button" @click="disableBackupOpen = false">{{ copy.common.cancel }}</button><button class="button danger" type="button" @click="disableBackup">{{ copy.settings.disable }}</button></template>
    </ModalDialog>
  </div>
</template>

<style scoped>
.app-frame{min-height:100vh;display:grid;grid-template-columns:236px minmax(0,1fr);background:var(--bg-app)}
.sidebar{position:sticky;top:0;height:100vh;padding:23px 18px 18px;display:flex;flex-direction:column;border-right:1px solid var(--border-subtle);background:linear-gradient(180deg,rgba(10,24,39,.98),rgba(6,16,27,.98));box-shadow:10px 0 40px rgba(0,0,0,.12)}
.sidebar :deep(.brand-lockup){padding:0 8px 22px;border-bottom:1px solid var(--border-subtle)}
.main-nav{display:flex;flex-direction:column;gap:5px;margin-top:23px}.nav-label{padding:0 11px 8px;color:var(--text-faint);font-size:10px;font-weight:750;letter-spacing:.14em;text-transform:uppercase}
.nav-item{position:relative;width:100%;min-height:44px;padding:0 12px;display:flex;align-items:center;gap:12px;border:1px solid transparent;border-radius:11px;background:transparent;color:var(--text-muted);font:inherit;font-size:13px;font-weight:650;text-decoration:none;cursor:pointer;transition:.18s ease}
.nav-item:hover{color:var(--text-strong);background:var(--surface-soft)}.nav-item.active{color:var(--cyan-200);border-color:rgba(45,212,226,.15);background:linear-gradient(90deg,rgba(25,188,209,.15),rgba(25,188,209,.04))}.nav-item.active:before{content:"";position:absolute;left:-19px;width:3px;height:24px;border-radius:0 4px 4px 0;background:var(--cyan-400);box-shadow:0 0 12px rgba(40,214,229,.65)}
.world-card{margin-top:25px;padding:14px;border:1px solid var(--border-subtle);border-radius:13px;background:linear-gradient(145deg,rgba(21,45,65,.7),rgba(10,26,42,.82))}.world-heading{display:flex;align-items:center;justify-content:space-between;color:var(--text-faint);font-size:10px;text-transform:uppercase;letter-spacing:.1em}.world-heading :deep(.status-pill){min-height:20px;padding:2px 6px;font-size:8px}.world-card>strong{display:block;margin:12px 0 7px;color:var(--text-strong);font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.world-source{display:flex;align-items:center;gap:6px;color:var(--text-muted);font-size:11px}.change-save{width:100%;display:flex;justify-content:space-between;align-items:center;margin-top:12px;padding:10px 0 0;border:0;border-top:1px solid var(--border-subtle);background:transparent;color:var(--cyan-300);font-size:11px;font-weight:650;cursor:pointer}
.sidebar-bottom{margin-top:auto}.settings-button{margin-bottom:12px}.build-info{display:flex;justify-content:space-between;padding:0 7px;color:var(--text-faint);font-size:9px}
.workspace{min-width:0;min-height:100vh}.topbar{height:82px;padding:0 30px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border-subtle);background:rgba(7,18,30,.78);backdrop-filter:blur(18px);position:sticky;top:0;z-index:30}.page-heading span{display:block;margin-bottom:5px;color:var(--cyan-400);font-size:9px;font-weight:750;letter-spacing:.16em;text-transform:uppercase}.page-heading h1{margin:0;color:var(--text-strong);font-size:20px;font-weight:720;letter-spacing:-.02em}.topbar-actions{display:flex;align-items:center;gap:10px}.search-box{width:270px;height:38px;display:flex;align-items:center;gap:9px;padding:0 12px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft);color:var(--text-faint)}.search-box:focus-within{border-color:var(--border-bright);color:var(--cyan-300)}.search-box input{width:100%;border:0;outline:0;background:transparent;color:var(--text);font:inherit;font-size:12px}.search-box input::placeholder{color:var(--text-faint)}.save-button:disabled,.button:disabled{opacity:.42;cursor:not-allowed;transform:none}.avatar{width:36px;height:36px;display:grid;place-items:center;border:1px solid rgba(224,187,98,.3);border-radius:10px;background:linear-gradient(145deg,rgba(224,187,98,.22),rgba(224,187,98,.07));color:var(--gold-200);font-size:11px;font-weight:800}.page-content{padding:26px 30px 38px;max-width:1510px;margin:0 auto}
.about-hero{display:flex;align-items:center;gap:16px;padding-bottom:18px}.about-hero img{width:62px;height:62px}.about-hero>div{display:flex;flex-direction:column;align-items:flex-start;gap:8px}.about-hero strong{color:var(--text-strong);font-size:17px}.setting-row{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:16px 0;border-top:1px solid var(--border-subtle)}.setting-row strong{color:var(--text-strong);font-size:13px}.setting-row p,.legal-block p{margin:5px 0 0;color:var(--text-muted);font-size:11px;line-height:1.6}.compact-button{font-size:11px;white-space:nowrap}.legal-block{margin-top:8px;padding:16px;border:1px solid var(--border-subtle);border-radius:12px;background:var(--surface-soft)}.legal-block>div{display:flex;justify-content:space-between;color:var(--text-muted);font-size:11px}.legal-block>div strong{color:var(--cyan-300)}.legal-block h3{margin:16px 0 0;color:var(--text-strong);font-size:13px}.toggle{width:44px;height:24px;padding:2px;border:1px solid var(--border-subtle);border-radius:99px;background:#122535;cursor:pointer}.toggle span{display:block;width:18px;height:18px;border-radius:50%;background:var(--text-faint);transition:.18s}.toggle.enabled{border-color:rgba(46,219,229,.35);background:rgba(34,199,216,.18)}.toggle.enabled span{transform:translateX(19px);background:var(--cyan-300)}.dialog-copy{margin:0 0 16px;color:var(--text-muted);font-size:12px;line-height:1.7}.path-confirm{padding:12px 14px;border:1px solid var(--border-subtle);border-radius:10px;background:rgba(3,13,22,.5)}.path-confirm span{display:block;margin-bottom:6px;color:var(--text-faint);font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.08em}.path-confirm code{display:block;overflow:hidden;color:#a7bdc6;font-size:10px;white-space:nowrap;text-overflow:ellipsis}.error-copy{color:var(--red-300);font-size:11px}
@media(max-width:1360px){.app-frame{grid-template-columns:218px minmax(0,1fr)}.sidebar{padding-left:14px;padding-right:14px}.page-content{padding:22px 24px}.topbar{padding:0 24px}.search-box{width:210px}.topbar-actions :deep(.status-pill){display:none}}
@media(max-width:1180px){.search-box{display:none}.save-button{padding:0 11px}.save-button .app-icon{display:none}}
</style>
