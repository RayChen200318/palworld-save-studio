<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import BrandLockup from '@/components/BrandLockup.vue'
import LanguageToggle from '@/components/LanguageToggle.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import StatusPill from '@/components/StatusPill.vue'
import { messages } from '@/i18n/messages'
import { apiClient } from '@/services/apiClient'
import { useCatalogStore } from '@/stores/catalog'
import { useCollectionStore } from '@/stores/collection'
import { useSessionStore } from '@/stores/session'
import type { PathContext } from '@/types/domain'

const router = useRouter()
const session = useSessionStore()
const catalog = useCatalogStore()
const collection = useCollectionStore()
const copy = computed(() => messages[session.locale])
const selectedPath = ref('')
const browserOpen = ref(false)
const browser = ref<PathContext | null>(null)
const browserBusy = ref(false)
const featureIcons = ['paw', 'spark', 'dna', 'bolt', 'briefcase', 'book']
const candidatePath = computed(() => selectedPath.value || session.config?.Path || session.session.Path || '')

async function ensureReady() {
  if (!session.initialized) await session.bootstrap()
}

async function openBrowser() {
  await ensureReady()
  browserBusy.value = true
  browserOpen.value = true
  try {
    browser.value = await apiClient.getPathContext()
  } finally {
    browserBusy.value = false
  }
}

async function browseTo(path: string) {
  browserBusy.value = true
  try {
    browser.value = await apiClient.browsePath(path)
  } finally {
    browserBusy.value = false
  }
}

async function browseBack() {
  browserBusy.value = true
  try {
    browser.value = await apiClient.pathBack()
  } finally {
    browserBusy.value = false
  }
}

function selectCurrentFolder() {
  if (!browser.value) return
  selectedPath.value = browser.value.currentPath
  browserOpen.value = false
}

async function detectSave() {
  await openBrowser()
  if (browser.value?.isPalDir) selectCurrentFolder()
}

async function openSave() {
  if (!candidatePath.value) {
    await openBrowser()
    return
  }
  await ensureReady()
  if (!await session.loadSave(candidatePath.value)) return
  collection.clear()
  await Promise.all([catalog.load(), collection.loadPals(true), collection.loadPlayers(true)])
  router.push('/dashboard')
}
</script>

<template>
  <div class="start-screen">
    <header class="start-header"><BrandLockup /><div class="header-actions"><StatusPill tone="cyan">{{ copy.common.beta }}</StatusPill><LanguageToggle /></div></header>
    <main class="start-main">
      <section class="hero-copy">
        <div class="eyebrow">{{ copy.start.eyebrow }}</div>
        <h1>{{ copy.start.title }}</h1>
        <p class="hero-intro">{{ copy.start.intro }}</p>
        <div class="hero-actions">
          <button class="button primary start-button" type="button" @click="openBrowser"><AppIcon name="folder" />{{ copy.start.choose }}</button>
          <button class="button ghost" type="button" @click="detectSave"><AppIcon name="search" />{{ copy.start.detect }}</button>
        </div>
        <div class="warning-note"><AppIcon name="alert" :size="18" /><div><strong>{{ copy.start.gameExitTitle }}</strong><span>{{ copy.start.gameExitCopy }}</span></div></div>
      </section>

      <section class="open-panel panel">
        <div class="panel-glow" />
        <div class="preview-top"><span class="eyebrow">{{ copy.start.candidate }}</span><StatusPill :tone="candidatePath ? 'green' : 'neutral'" dot>{{ candidatePath ? 'Palworld 1.0' : '—' }}</StatusPill></div>
        <div class="save-title-row"><div class="save-icon"><AppIcon name="file" :size="26" /></div><div><h2>{{ candidatePath ? (candidatePath.split(/[\\/]/).filter(Boolean).at(-1) || 'Palworld Save') : copy.nav.noWorld }}</h2><p>{{ candidatePath ? copy.start.compatible : copy.start.notSave }}</p></div></div>
        <div class="path-box"><span>{{ copy.start.pathLabel }}</span><code>{{ candidatePath || '—' }}</code></div>
        <p v-if="session.error" class="load-error"><AppIcon name="alert" :size="16" />{{ session.error }}</p>
        <div class="preview-actions"><button class="button secondary" type="button" @click="openBrowser">{{ copy.start.browse }}</button><button class="button primary" type="button" :disabled="session.busy" @click="openSave">{{ session.busy ? copy.common.loading : copy.start.open }}<AppIcon name="arrow-right" :size="17" /></button></div>
      </section>
    </main>

    <section class="feature-section">
      <div class="feature-title"><span class="eyebrow">{{ copy.start.featuresTitle }}</span></div>
      <div class="feature-grid">
        <article v-for="(name, index) in copy.start.featureNames" :key="name" class="feature-card"><span><AppIcon :name="featureIcons[index]" :size="20" /></span><div><strong>{{ name }}</strong><p>{{ copy.start.featureCopy[index] }}</p></div></article>
      </div>
    </section>

    <ModalDialog :open="browserOpen" :title="copy.start.browseTitle" width="760px" @close="browserOpen = false">
      <div class="browser-path"><span>{{ copy.start.currentFolder }}</span><code>{{ browser?.currentPath || '—' }}</code></div>
      <div class="browser-tools"><button class="button secondary" type="button" :disabled="browserBusy" @click="browseBack"><AppIcon name="arrow-left" :size="15" />{{ copy.start.up }}</button><StatusPill :tone="browser?.isPalDir ? 'green' : 'neutral'">{{ browser?.isPalDir ? copy.start.compatible : copy.start.notSave }}</StatusPill></div>
      <div class="folder-list">
        <button v-for="(child, path) in browser?.children" v-show="child.isDir" :key="path" type="button" @click="browseTo(path)"><AppIcon name="folder" :size="17" /><span>{{ child.filename }}</span><AppIcon name="chevron" :size="14" /></button>
        <p v-if="browser && !Object.values(browser.children).some((child) => child.isDir)">{{ copy.start.emptyFolder }}</p>
      </div>
      <template #footer><button class="button secondary" type="button" @click="browserOpen = false">{{ copy.common.cancel }}</button><button class="button primary" type="button" :disabled="!browser?.isPalDir" @click="selectCurrentFolder">{{ copy.start.useFolder }}</button></template>
    </ModalDialog>
  </div>
</template>

<style scoped>
.start-screen{position:relative;min-height:100vh;overflow:hidden;background:radial-gradient(circle at 78% 20%,rgba(53,230,209,.14),transparent 30%),radial-gradient(circle at 18% 88%,rgba(139,124,255,.12),transparent 32%),linear-gradient(145deg,#080b14,#0c1220 58%,#080b14)}
.start-screen:before{content:"";position:absolute;inset:0;pointer-events:none;opacity:.16;background-image:linear-gradient(rgba(164,188,221,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(164,188,221,.08) 1px,transparent 1px);background-size:56px 56px;mask-image:linear-gradient(to right,transparent,black 48%,transparent)}
.start-header{position:relative;z-index:3;height:68px;max-width:1480px;margin:0 auto;padding:0 40px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border-subtle);background:rgba(8,11,20,.34);backdrop-filter:blur(var(--glass-blur))}.header-actions{display:flex;align-items:center;gap:10px}
.start-main{position:relative;z-index:2;max-width:1420px;margin:0 auto;padding:30px 48px 22px;display:grid;grid-template-columns:minmax(390px,.85fr) minmax(480px,1.15fr);align-items:center;gap:48px}.hero-copy h1{max-width:620px;margin:12px 0 14px;color:var(--text-strong);font-size:40px;line-height:1.12;letter-spacing:-.045em;font-weight:750}.hero-intro{max-width:580px;margin:0;color:var(--text-muted);font-size:15px;line-height:1.65}.hero-actions{display:flex;align-items:center;gap:10px;margin-top:20px}.start-button{min-height:44px;padding:0 20px}.warning-note{max-width:540px;margin-top:18px;padding:12px 14px;display:flex;align-items:flex-start;gap:11px;border:1px solid rgba(242,198,109,.18);border-left:3px solid var(--gold-300);border-radius:9px;background:rgba(242,198,109,.06);color:var(--gold-300)}.warning-note div{display:flex;flex-direction:column;gap:3px}.warning-note strong{font-size:13px}.warning-note span{color:var(--text-muted);font-size:13px;line-height:1.5}
.open-panel{position:relative;padding:22px;overflow:hidden;box-shadow:var(--shadow-float)}.panel-glow{position:absolute;inset:0 0 auto;height:2px;background:linear-gradient(90deg,transparent,var(--cyan-300),var(--violet-300),transparent)}.preview-top{display:flex;align-items:center;justify-content:space-between}.save-title-row{display:flex;align-items:center;gap:16px;margin:22px 0 18px}.save-icon{width:58px;height:58px;display:grid;place-items:center;border:1px solid rgba(53,230,209,.24);border-radius:14px;background:linear-gradient(145deg,rgba(53,230,209,.12),rgba(139,124,255,.1));color:var(--cyan-300)}.save-title-row h2{margin:0 0 5px;color:var(--text-strong);font-size:18px}.save-title-row p{margin:0;color:var(--text-muted);font-size:13px}.path-box,.browser-path{padding:13px 14px;border:1px solid var(--border-subtle);border-radius:10px;background:rgba(5,9,17,.56)}.path-box span,.browser-path span{display:block;margin-bottom:6px;color:var(--text-faint);font-size:12px;font-weight:700}.path-box code,.browser-path code{display:block;overflow:hidden;color:var(--text-muted);font-size:11px;white-space:nowrap;text-overflow:ellipsis}.preview-actions{margin-top:20px;display:flex;justify-content:flex-end;gap:10px}.load-error{display:flex;gap:8px;margin:12px 0 0;color:var(--red-300);font-size:13px;line-height:1.5}.button:disabled{opacity:.42;cursor:not-allowed;transform:none}
.feature-section{position:relative;z-index:2;max-width:1420px;margin:0 auto;padding:4px 48px 28px}.feature-title{margin-bottom:10px}.feature-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.feature-card{min-height:82px;padding:13px 14px;display:flex;align-items:flex-start;gap:12px;border:1px solid var(--border-subtle);border-radius:12px;background:rgba(20,30,48,.66);backdrop-filter:blur(10px)}.feature-card:hover{border-color:rgba(139,124,255,.32);background:rgba(20,30,48,.82);transform:translateY(-1px)}.feature-card>span{width:38px;height:38px;flex:0 0 38px;display:grid;place-items:center;border-radius:10px;background:linear-gradient(145deg,rgba(53,230,209,.12),rgba(139,124,255,.1));color:var(--cyan-300)}.feature-card strong{display:block;color:var(--text-strong);font-size:15px}.feature-card p{margin:4px 0 0;color:var(--text-muted);font-size:13px;line-height:1.45}
.browser-tools{display:flex;align-items:center;justify-content:space-between;margin:14px 0}.folder-list{height:330px;overflow:auto;border:1px solid var(--border-subtle);border-radius:12px;background:rgba(5,9,17,.42)}.folder-list button{width:100%;height:46px;padding:0 14px;display:flex;align-items:center;gap:10px;border:0;border-bottom:1px solid var(--border-subtle);background:transparent;color:var(--text);font-size:14px;text-align:left;cursor:pointer}.folder-list button:hover{background:var(--surface-hover);color:var(--cyan-200)}.folder-list button span{flex:1}.folder-list p{padding:24px;color:var(--text-muted);font-size:13px;text-align:center}
@media(max-width:1366px){.start-header{padding:0 32px}.start-main{padding:24px 36px 18px;grid-template-columns:minmax(350px,.8fr) minmax(440px,1.2fr);gap:34px}.feature-section{padding:2px 36px 24px}.feature-card{min-height:78px}}
@media(max-height:780px){.start-main{padding-top:18px;padding-bottom:14px}.hero-copy h1{margin-top:8px;margin-bottom:10px}.hero-actions{margin-top:14px}.warning-note{margin-top:12px;padding-top:9px;padding-bottom:9px}.feature-card{min-height:72px}.feature-section{padding-bottom:18px}}
</style>
