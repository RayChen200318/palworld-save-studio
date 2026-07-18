<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from './AppIcon.vue'
import BrandLockup from './BrandLockup.vue'
import LanguageToggle from './LanguageToggle.vue'
import ModalDialog from './ModalDialog.vue'
import StatusPill from './StatusPill.vue'
import { messages } from '@/i18n/messages'
import { mockSave } from '@/mocks/session'
import { usePrototypeStore } from '@/stores/prototype'

defineProps<{ eyebrow: string; title: string }>()

const route = useRoute()
const store = usePrototypeStore()
const copy = computed(() => messages[store.locale])
const aboutOpen = ref(false)
const checked = ref(false)
const active = computed(() => route.name === 'pal-detail' ? 'pals' : 'dashboard')
</script>

<template>
  <div class="app-frame">
    <aside class="sidebar">
      <BrandLockup />

      <nav class="main-nav" :aria-label="copy.nav.overview">
        <span class="nav-label">{{ copy.nav.overview }}</span>
        <RouterLink to="/dashboard" class="nav-item" :class="{ active: active === 'dashboard' }">
          <AppIcon name="grid" /><span>{{ copy.nav.dashboard }}</span>
        </RouterLink>
        <button class="nav-item disabled" type="button">
          <AppIcon name="users" /><span>{{ copy.nav.players }}</span><small>{{ copy.common.comingSoon }}</small>
        </button>
        <RouterLink to="/pals/WorldTreeDragon" class="nav-item" :class="{ active: active === 'pals' }">
          <AppIcon name="paw" /><span>{{ copy.nav.pals }}</span>
        </RouterLink>
      </nav>

      <div class="world-card">
        <div class="world-heading"><span>{{ copy.nav.loadedWorld }}</span><StatusPill tone="green" dot>LIVE</StatusPill></div>
        <strong>{{ mockSave.name[store.locale] }}</strong>
        <div class="world-source"><AppIcon name="server" :size="15" />{{ mockSave.source }}</div>
        <RouterLink to="/" class="change-save">{{ copy.nav.changeSave }}<AppIcon name="chevron" :size="14" /></RouterLink>
      </div>

      <div class="sidebar-bottom">
        <button class="nav-item settings-button" type="button" @click="aboutOpen = true">
          <AppIcon name="settings" /><span>{{ copy.nav.settings }}</span>
        </button>
        <div class="build-info"><span>{{ copy.common.version }}</span><span>{{ copy.common.unofficial }}</span></div>
      </div>
    </aside>

    <div class="workspace">
      <header class="topbar">
        <div class="page-heading"><span>{{ eyebrow }}</span><h1>{{ title }}</h1></div>
        <div class="topbar-actions">
          <label class="search-box"><AppIcon name="search" :size="18" /><input :placeholder="store.locale === 'zh-CN' ? '搜索玩家或帕鲁' : 'Search players or Pals'" /></label>
          <LanguageToggle />
          <div class="avatar">RC</div>
        </div>
      </header>
      <main class="page-content"><slot /></main>
    </div>

    <ModalDialog :open="aboutOpen" :title="copy.about.title" width="600px" @close="aboutOpen = false">
      <div class="about-hero">
        <img src="/brand/palworld-save-studio-logo.svg" alt="" />
        <div><strong>{{ copy.about.subtitle }}</strong><StatusPill tone="cyan">{{ copy.common.beta }}</StatusPill></div>
      </div>
      <div class="setting-row">
        <div><strong>{{ copy.about.language }}</strong><p>简体中文 / English</p></div><LanguageToggle />
      </div>
      <div class="setting-row">
        <div><strong>{{ copy.about.update }}</strong><p>{{ copy.about.updateHint }}</p></div>
        <button class="button secondary compact-button" type="button" @click="checked = true">{{ checked ? (store.locale === 'zh-CN' ? '已是最新预览版' : 'Preview is current') : copy.about.check }}</button>
      </div>
      <div class="legal-block">
        <div><span>{{ copy.about.maintainer }}</span><strong>{{ copy.about.maintainerName }}</strong></div>
        <h3>{{ copy.about.license }}</h3><p>{{ copy.about.legal }}</p><p>{{ copy.about.disclaimer }}</p>
      </div>
      <template #footer><button class="button primary" type="button" @click="aboutOpen = false">{{ copy.common.close }}</button></template>
    </ModalDialog>
  </div>
</template>

<style scoped>
.app-frame{min-height:100vh;display:grid;grid-template-columns:236px minmax(0,1fr);background:var(--bg-app)}
.sidebar{position:sticky;top:0;height:100vh;padding:23px 18px 18px;display:flex;flex-direction:column;border-right:1px solid var(--border-subtle);background:linear-gradient(180deg,rgba(10,24,39,.98),rgba(6,16,27,.98));box-shadow:10px 0 40px rgba(0,0,0,.12)}
.sidebar :deep(.brand-lockup){padding:0 8px 22px;border-bottom:1px solid var(--border-subtle)}
.main-nav{display:flex;flex-direction:column;gap:5px;margin-top:23px}.nav-label{padding:0 11px 8px;color:var(--text-faint);font-size:10px;font-weight:750;letter-spacing:.14em;text-transform:uppercase}
.nav-item{position:relative;width:100%;min-height:44px;padding:0 12px;display:flex;align-items:center;gap:12px;border:1px solid transparent;border-radius:11px;background:transparent;color:var(--text-muted);font:inherit;font-size:13px;font-weight:650;text-decoration:none;cursor:pointer;transition:.18s ease}
.nav-item:hover:not(.disabled){color:var(--text-strong);background:var(--surface-soft)}.nav-item.active{color:var(--cyan-200);border-color:rgba(45,212,226,.15);background:linear-gradient(90deg,rgba(25,188,209,.15),rgba(25,188,209,.04))}.nav-item.active:before{content:"";position:absolute;left:-19px;width:3px;height:24px;border-radius:0 4px 4px 0;background:var(--cyan-400);box-shadow:0 0 12px rgba(40,214,229,.65)}
.nav-item small{margin-left:auto;padding:3px 6px;border-radius:6px;background:rgba(255,255,255,.04);color:var(--text-faint);font-size:8px;letter-spacing:.04em}.nav-item.disabled{opacity:.48;cursor:default}
.world-card{margin-top:25px;padding:14px;border:1px solid var(--border-subtle);border-radius:13px;background:linear-gradient(145deg,rgba(21,45,65,.7),rgba(10,26,42,.82))}.world-heading{display:flex;align-items:center;justify-content:space-between;color:var(--text-faint);font-size:10px;text-transform:uppercase;letter-spacing:.1em}.world-heading :deep(.status-pill){min-height:20px;padding:2px 6px;font-size:8px}.world-card>strong{display:block;margin:12px 0 7px;color:var(--text-strong);font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.world-source{display:flex;align-items:center;gap:6px;color:var(--text-muted);font-size:11px}.change-save{display:flex;justify-content:space-between;align-items:center;margin-top:12px;padding-top:10px;border-top:1px solid var(--border-subtle);color:var(--cyan-300);font-size:11px;font-weight:650;text-decoration:none}
.sidebar-bottom{margin-top:auto}.settings-button{margin-bottom:12px}.build-info{display:flex;justify-content:space-between;padding:0 7px;color:var(--text-faint);font-size:9px}
.workspace{min-width:0;min-height:100vh}.topbar{height:82px;padding:0 30px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border-subtle);background:rgba(7,18,30,.78);backdrop-filter:blur(18px);position:sticky;top:0;z-index:30}.page-heading span{display:block;margin-bottom:5px;color:var(--cyan-400);font-size:9px;font-weight:750;letter-spacing:.16em;text-transform:uppercase}.page-heading h1{margin:0;color:var(--text-strong);font-size:20px;font-weight:720;letter-spacing:-.02em}.topbar-actions{display:flex;align-items:center;gap:10px}.search-box{width:240px;height:38px;display:flex;align-items:center;gap:9px;padding:0 12px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft);color:var(--text-faint)}.search-box:focus-within{border-color:var(--border-bright);color:var(--cyan-300)}.search-box input{width:100%;border:0;outline:0;background:transparent;color:var(--text);font:inherit;font-size:12px}.search-box input::placeholder{color:var(--text-faint)}.avatar{width:36px;height:36px;display:grid;place-items:center;border:1px solid rgba(224,187,98,.3);border-radius:10px;background:linear-gradient(145deg,rgba(224,187,98,.22),rgba(224,187,98,.07));color:var(--gold-200);font-size:11px;font-weight:800}.page-content{padding:26px 30px 38px;max-width:1510px;margin:0 auto}
.about-hero{display:flex;align-items:center;gap:16px;padding-bottom:18px}.about-hero img{width:62px;height:62px}.about-hero>div{display:flex;flex-direction:column;align-items:flex-start;gap:8px}.about-hero strong{color:var(--text-strong);font-size:17px}.setting-row{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:16px 0;border-top:1px solid var(--border-subtle)}.setting-row strong{color:var(--text-strong);font-size:13px}.setting-row p,.legal-block p{margin:5px 0 0;color:var(--text-muted);font-size:11px;line-height:1.6}.compact-button{font-size:11px;white-space:nowrap}.legal-block{margin-top:8px;padding:16px;border:1px solid var(--border-subtle);border-radius:12px;background:var(--surface-soft)}.legal-block>div{display:flex;justify-content:space-between;color:var(--text-muted);font-size:11px}.legal-block>div strong{color:var(--cyan-300)}.legal-block h3{margin:16px 0 0;color:var(--text-strong);font-size:13px}
@media(max-width:1360px){.app-frame{grid-template-columns:218px minmax(0,1fr)}.sidebar{padding-left:14px;padding-right:14px}.page-content{padding:22px 24px}.topbar{padding:0 24px}.search-box{width:200px}}
@media(max-width:1100px){.search-box{display:none}}
</style>
