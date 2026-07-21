<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from './AppIcon.vue'
import BrandLockup from './BrandLockup.vue'
import LanguageToggle from './LanguageToggle.vue'
import ModalDialog from './ModalDialog.vue'
import StatusPill from './StatusPill.vue'
import { messages } from '@/i18n/messages'
import { useCollectionStore } from '@/stores/collection'
import { useDraftStore } from '@/stores/draft'
import { useSessionStore } from '@/stores/session'
import { useItemsStore } from '@/stores/items'
import type { CommitPreview } from '@/types/domain'

defineProps<{ eyebrow: string; title: string }>()

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const draft = useDraftStore()
const collection = useCollectionStore()
const items = useItemsStore()
const brandLogoUrl = '/brand/palworld-save-studio-logo.svg'
const copy = computed(() => messages[session.locale])
const settingsOpen = ref(false)
const disableBackupOpen = ref(false)
const saveOpen = ref(false)
const changeOpen = ref(false)
const commitPreview = ref<CommitPreview | null>(null)
const serverStoppedConfirmed = ref(false)
const active = computed(() => String(route.name || '').split('-')[0])
const searchVisible = computed(() => active.value === 'pals')

function requestChangeSave() {
  if (session.dirty) changeOpen.value = true
  else router.push('/')
}

async function discardAndChange() {
  await session.discardDraft()
  collection.clear()
  items.clear()
  changeOpen.value = false
  router.push('/')
}

async function openSaveDialog() {
  if (!draft.canCommit) return
  commitPreview.value = null
  try {
    commitPreview.value = await session.previewCommit()
    serverStoppedConfirmed.value = false
    saveOpen.value = true
  } catch {
    saveOpen.value = true
  }
}

async function commit() {
  if (!draft.canCommit) return
  if (session.session.SaveKind === 'dedicated' && !serverStoppedConfirmed.value) return
  await session.commitDraft(serverStoppedConfirmed.value)
  saveOpen.value = false
  await Promise.all([collection.loadPals(true), collection.loadPlayers(true)])
  if (items.selectedPlayerId) await items.loadInventory(items.selectedPlayerId, true)
}

async function toggleBackup() {
  if (session.session.BackupRequired) return
  if (session.session.BackupEnabled) disableBackupOpen.value = true
  else await session.setBackupEnabled(true)
}

async function disableBackup() {
  await session.setBackupEnabled(false)
  disableBackupOpen.value = false
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
        <RouterLink to="/items" class="nav-item" :class="{ active: active === 'items' }"><AppIcon name="box" /><span>{{ copy.nav.items }}</span></RouterLink>
      </nav>

      <div class="world-card">
        <div class="world-heading"><span>{{ copy.nav.loadedWorld }}</span><StatusPill tone="green" dot>{{ session.session.SaveKind === 'dedicated' ? copy.start.dedicatedSave : copy.start.localSave }}</StatusPill></div>
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
          <button class="button primary save-button" type="button" :disabled="!draft.canCommit || session.busy" @click="openSaveDialog"><AppIcon name="save" :size="16" />{{ session.busy ? copy.common.saving : copy.common.save }}</button>
          <LanguageToggle />
          <div class="avatar">RC</div>
        </div>
      </header>
      <main class="page-content"><slot /></main>
    </div>

    <ModalDialog :open="saveOpen" :title="copy.dialogs.saveTitle" @close="saveOpen = false">
      <div class="path-confirm"><span>{{ copy.dialogs.target }}</span><code>{{ session.session.Path }}</code></div>
      <div v-if="commitPreview" class="commit-summary">
        <div><span>{{ copy.dialogs.worldId }}</span><code>{{ commitPreview.WorldId }}</code></div>
        <div><span>{{ copy.dialogs.backupTarget }}</span><code>{{ commitPreview.BackupPath }}</code></div>
        <section><strong>{{ copy.dialogs.filesChanged }}</strong><code v-for="path in commitPreview.FilesChanged" :key="`changed-${path}`">{{ path }}</code><small v-if="!commitPreview.FilesChanged.length">{{ copy.common.none }}</small></section>
        <section><strong>{{ copy.dialogs.filesSkipped }}</strong><code v-for="path in commitPreview.FilesSkipped" :key="`skipped-${path}`">{{ path }}</code><small v-if="!commitPreview.FilesSkipped.length">{{ copy.common.none }}</small></section>
      </div>
      <label v-if="session.session.SaveKind === 'dedicated'" class="server-confirm"><input v-model="serverStoppedConfirmed" type="checkbox" /><span><strong>{{ copy.dialogs.serverStopped }}</strong><small>{{ copy.dialogs.serverStoppedHint }}</small></span></label>
      <p v-if="session.error" class="error-copy">{{ session.error }}</p>
      <template #footer><button class="button secondary" type="button" @click="saveOpen = false">{{ copy.common.cancel }}</button><button class="button primary" type="button" :disabled="draft.pending || session.busy || !commitPreview || (session.session.SaveKind === 'dedicated' && !serverStoppedConfirmed)" @click="commit">{{ copy.common.save }}</button></template>
    </ModalDialog>

    <ModalDialog :open="changeOpen" :title="copy.dialogs.changeTitle" @close="changeOpen = false">
      <p class="dialog-copy">{{ copy.dialogs.changeCopy }}</p>
      <template #footer><button class="button secondary" type="button" @click="changeOpen = false">{{ copy.common.cancel }}</button><button class="button danger" type="button" @click="discardAndChange">{{ copy.dialogs.discard }}</button></template>
    </ModalDialog>

    <ModalDialog :open="settingsOpen" :title="copy.settings.title" width="620px" @close="settingsOpen = false">
      <div class="about-hero"><img :src="brandLogoUrl" alt="" /><div><strong>Palworld Save Studio</strong><StatusPill tone="cyan">{{ copy.common.beta }}</StatusPill></div></div>
      <div class="setting-row"><div><strong>{{ copy.settings.language }}</strong><p>简体中文 / English</p></div><LanguageToggle /></div>
      <div class="setting-row"><div><strong>{{ copy.settings.backup }}</strong><p>{{ session.session.BackupRequired ? copy.settings.backupRequiredHint : copy.settings.backupHint }}</p></div><button class="toggle" :class="{ enabled: session.session.BackupEnabled }" type="button" :aria-pressed="session.session.BackupEnabled" :disabled="session.session.BackupRequired" @click="toggleBackup"><span /></button></div>
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
.app-frame{min-height:100vh;display:grid;grid-template-columns:212px minmax(0,1fr);background:var(--bg-app)}
.sidebar{position:sticky;top:0;height:100vh;padding:20px 14px 16px;display:flex;flex-direction:column;border-right:1px solid var(--border-subtle);background:rgba(9,14,25,.86);backdrop-filter:blur(var(--glass-blur));box-shadow:10px 0 36px rgba(0,0,0,.18)}
.sidebar :deep(.brand-lockup){padding:0 6px 18px;border-bottom:1px solid var(--border-subtle)}
.main-nav{display:flex;flex-direction:column;gap:4px;margin-top:18px}.nav-label{padding:0 10px 7px;color:var(--text-faint);font-size:12px;font-weight:750;letter-spacing:.06em}
.nav-item{position:relative;width:100%;min-height:44px;padding:0 11px;display:flex;align-items:center;gap:11px;border:1px solid transparent;border-radius:10px;background:transparent;color:var(--text-muted);font:inherit;font-size:14px;font-weight:650;text-decoration:none;cursor:pointer;transition-property:color,background,border-color,transform}
.nav-item:hover{color:var(--text-strong);background:var(--surface-soft)}.nav-item.active{color:var(--cyan-200);border-color:rgba(139,124,255,.2);background:linear-gradient(90deg,rgba(53,230,209,.12),rgba(139,124,255,.08))}.nav-item.active:before{content:"";position:absolute;left:-15px;width:3px;height:24px;border-radius:0 4px 4px 0;background:linear-gradient(var(--cyan-300),var(--violet-300));box-shadow:0 0 12px rgba(53,230,209,.36)}
.world-card{margin-top:20px;padding:13px;border:1px solid var(--border-subtle);border-radius:12px;background:linear-gradient(145deg,rgba(20,30,48,.82),rgba(13,20,34,.68));box-shadow:0 12px 30px rgba(0,0,0,.16)}.world-heading{display:flex;align-items:center;justify-content:space-between;color:var(--text-faint);font-size:12px;font-weight:650}.world-heading :deep(.status-pill){min-height:24px;padding:2px 7px;font-size:12px}.world-card>strong{display:block;margin:11px 0 6px;color:var(--text-strong);font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.world-source{display:flex;align-items:center;gap:6px;color:var(--text-muted);font-size:12px}.change-save{width:100%;display:flex;justify-content:space-between;align-items:center;margin-top:11px;padding:10px 0 0;border:0;border-top:1px solid var(--border-subtle);background:transparent;color:var(--cyan-300);font-size:12px;font-weight:700;cursor:pointer}
.sidebar-bottom{margin-top:auto}.settings-button{margin-bottom:10px}.build-info{display:grid;gap:2px;padding:0 7px;color:var(--text-faint);font-size:12px}
.workspace{min-width:0;min-height:100vh}.topbar{height:68px;padding:0 24px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border-subtle);background:rgba(8,11,20,.76);backdrop-filter:blur(var(--glass-blur));position:sticky;top:0;z-index:30}.page-heading span{display:block;margin-bottom:1px;color:var(--cyan-300);font-size:12px;font-weight:750;letter-spacing:.07em}.page-heading h1{margin:0;color:var(--text-strong);font-size:28px;font-weight:720;line-height:1.1;letter-spacing:-.03em}.topbar-actions{display:flex;align-items:center;gap:8px}.search-box{width:260px;height:40px;display:flex;align-items:center;gap:9px;padding:0 12px;border:1px solid var(--border-subtle);border-radius:10px;background:rgba(20,30,48,.66);color:var(--text-faint)}.search-box:focus-within{border-color:var(--border-bright);color:var(--cyan-300)}.search-box input{width:100%;border:0;outline:0;background:transparent;color:var(--text);font:inherit;font-size:14px}.search-box input::placeholder{color:var(--text-faint)}.save-button:disabled,.button:disabled{opacity:.42;cursor:not-allowed;transform:none}.avatar{width:38px;height:38px;display:grid;place-items:center;border:1px solid rgba(139,124,255,.34);border-radius:10px;background:linear-gradient(145deg,rgba(139,124,255,.24),rgba(53,230,209,.08));color:var(--violet-200);font-size:12px;font-weight:800}.page-content{width:100%;max-width:1720px;margin:0 auto;padding:24px 24px 32px}
.about-hero{display:flex;align-items:center;gap:16px;padding-bottom:18px}.about-hero img{width:64px;height:64px}.about-hero>div{display:flex;flex-direction:column;align-items:flex-start;gap:8px}.about-hero strong{color:var(--text-strong);font-size:18px}.setting-row{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:16px 0;border-top:1px solid var(--border-subtle)}.setting-row strong{color:var(--text-strong);font-size:15px}.setting-row p,.legal-block p{margin:4px 0 0;color:var(--text-muted);font-size:13px;line-height:1.6}.legal-block{margin-top:8px;padding:16px;border:1px solid var(--border-subtle);border-radius:12px;background:var(--surface-soft)}.legal-block>div{display:flex;justify-content:space-between;color:var(--text-muted);font-size:13px}.legal-block>div strong{color:var(--cyan-300)}.legal-block h3{margin:16px 0 0;color:var(--text-strong);font-size:15px}.toggle{width:46px;height:26px;padding:2px;border:1px solid var(--border-subtle);border-radius:99px;background:#121a2a;cursor:pointer}.toggle span{display:block;width:20px;height:20px;border-radius:50%;background:var(--text-faint);transition:transform 160ms ease,background 160ms ease}.toggle.enabled{border-color:rgba(53,230,209,.35);background:rgba(53,230,209,.15)}.toggle.enabled span{transform:translateX(19px);background:var(--cyan-300)}.dialog-copy{margin:0 0 16px;color:var(--text-muted);font-size:14px;line-height:1.7}.path-confirm{padding:13px 14px;border:1px solid var(--border-subtle);border-radius:10px;background:rgba(5,9,17,.56)}.path-confirm span{display:block;margin-bottom:6px;color:var(--text-faint);font-size:12px;font-weight:700}.path-confirm code{display:block;overflow:hidden;color:var(--text-muted);font-size:11px;white-space:nowrap;text-overflow:ellipsis}.error-copy{color:var(--red-300);font-size:13px}
.commit-summary{margin-top:10px;display:grid;gap:8px}.commit-summary>div,.commit-summary section{padding:10px 12px;border:1px solid var(--border-subtle);border-radius:9px;background:var(--surface-soft)}.commit-summary span,.commit-summary strong{display:block;margin-bottom:5px;color:var(--text-faint);font-size:12px}.commit-summary code,.commit-summary small{display:block;color:var(--text-muted);font-size:11px;line-height:1.55;overflow-wrap:anywhere}.server-confirm{margin-top:12px;padding:12px;display:flex;align-items:flex-start;gap:10px;border:1px solid rgba(242,198,109,.3);border-radius:9px;background:rgba(242,198,109,.07);cursor:pointer}.server-confirm input{margin-top:3px}.server-confirm strong,.server-confirm small{display:block}.server-confirm strong{color:var(--gold-300);font-size:13px}.server-confirm small{margin-top:3px;color:var(--text-muted);font-size:12px;line-height:1.5}.toggle:disabled{opacity:.65;cursor:not-allowed}
@media(max-width:1366px){.app-frame{grid-template-columns:200px minmax(0,1fr)}.sidebar{padding-left:12px;padding-right:12px}.page-content{padding:20px 20px 28px}.topbar{padding:0 20px}.search-box{width:205px}.topbar-actions :deep(.status-pill){display:none}}
@media(max-width:1180px){.search-box{display:none}.save-button{padding:0 11px}.save-button .app-icon{display:none}}
</style>
