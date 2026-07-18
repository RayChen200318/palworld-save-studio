<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import BrandLockup from '@/components/BrandLockup.vue'
import LanguageToggle from '@/components/LanguageToggle.vue'
import StatusPill from '@/components/StatusPill.vue'
import { messages } from '@/i18n/messages'
import { mockSave } from '@/mocks/session'
import { usePrototypeStore } from '@/stores/prototype'

const router = useRouter()
const store = usePrototypeStore()
const copy = computed(() => messages[store.locale])
const detected = ref(true)

function openSave() {
  store.openMockSave()
  router.push('/dashboard')
}
</script>

<template>
  <div class="start-screen">
    <header class="start-header">
      <BrandLockup />
      <div class="header-actions"><StatusPill tone="cyan">{{ copy.common.beta }}</StatusPill><LanguageToggle /></div>
    </header>

    <main class="start-main">
      <section class="hero-copy">
        <div class="eyebrow">{{ copy.start.eyebrow }}</div>
        <h1>{{ copy.start.titleA }}<br /><span>{{ copy.start.titleB }}</span></h1>
        <p class="hero-intro">{{ copy.start.intro }}</p>
        <div class="hero-actions">
          <button class="button primary start-button" type="button" @click="detected = true"><AppIcon name="folder" />{{ copy.start.choose }}</button>
          <button class="button ghost" type="button" @click="detected = true"><AppIcon name="search" />{{ copy.start.detect }}</button>
        </div>
        <div class="warning-note"><AppIcon name="alert" :size="18" /><div><strong>{{ copy.start.warningTitle }}</strong><span>{{ copy.start.warningCopy }}</span></div></div>
      </section>

      <section class="save-preview-wrap">
        <div class="crystal-orbit orbit-one"></div><div class="crystal-orbit orbit-two"></div>
        <article class="save-preview panel" :class="{ detected }">
          <div class="preview-top">
            <span class="eyebrow">{{ copy.start.preview }}</span>
            <StatusPill tone="green" dot>{{ copy.start.detected }}</StatusPill>
          </div>
          <div class="save-title-row">
            <div class="save-icon"><AppIcon name="file" :size="25" /></div>
            <div><h2>{{ copy.start.world }}</h2><p>{{ copy.start.detectedHint }}</p></div>
          </div>
          <div class="path-box"><span>{{ copy.start.pathLabel }}</span><code>{{ mockSave.path }}</code></div>
          <dl class="save-meta">
            <div><dt>{{ copy.start.buildLabel }}</dt><dd><AppIcon name="check" :size="15" />{{ copy.start.buildValue }}</dd></div>
            <div><dt>{{ copy.start.sourceLabel }}</dt><dd><AppIcon name="server" :size="15" />{{ copy.start.sourceValue }}</dd></div>
          </dl>
          <div class="safety-row"><div class="shield-badge"><AppIcon name="shield" :size="22" /></div><div><strong>{{ copy.start.safetyTitle }}</strong><p>{{ copy.start.safetyCopy }}</p></div></div>
          <div class="preview-actions">
            <button class="button secondary" type="button">{{ copy.start.browse }}</button>
            <button class="button primary" type="button" @click="openSave">{{ copy.start.continue }}<AppIcon name="arrow-right" :size="17" /></button>
          </div>
        </article>
      </section>
    </main>

    <footer class="trust-strip">
      <div><span class="trust-icon"><AppIcon name="shield" /></span><section><strong>{{ copy.start.localTitle }}</strong><p>{{ copy.start.localCopy }}</p></section></div>
      <div><span class="trust-icon"><AppIcon name="server" /></span><section><strong>{{ copy.start.compatibleTitle }}</strong><p>{{ copy.start.compatibleCopy }}</p></section></div>
      <div class="build-stamp"><span>{{ copy.common.version }}</span><small>{{ copy.common.unofficial }}</small></div>
    </footer>
  </div>
</template>

<style scoped>
.start-screen{position:relative;min-height:100vh;overflow:hidden;background:radial-gradient(circle at 75% 34%,rgba(25,189,210,.13),transparent 29%),radial-gradient(circle at 21% 95%,rgba(206,165,72,.045),transparent 30%),linear-gradient(145deg,#06111e,#081725 58%,#06101c)}
.start-screen:before{content:"";position:absolute;inset:0;pointer-events:none;opacity:.18;background-image:linear-gradient(rgba(88,170,194,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(88,170,194,.08) 1px,transparent 1px);background-size:52px 52px;mask-image:linear-gradient(to right,transparent,black 55%,transparent)}
.start-header{position:relative;z-index:3;height:84px;max-width:1480px;margin:0 auto;padding:0 52px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border-subtle)}.header-actions{display:flex;align-items:center;gap:10px}
.start-main{position:relative;z-index:2;max-width:1480px;min-height:calc(100vh - 204px);margin:0 auto;padding:50px 64px 42px;display:grid;grid-template-columns:minmax(460px,.9fr) minmax(500px,1fr);align-items:center;gap:78px}
.hero-copy{padding-bottom:10px}.hero-copy h1{margin:17px 0 19px;color:var(--text-strong);font-size:48px;line-height:1.17;letter-spacing:-.045em;font-weight:740}.hero-copy h1 span{color:var(--cyan-200);text-shadow:0 0 28px rgba(43,213,228,.13)}.hero-intro{max-width:590px;margin:0;color:var(--text-muted);font-size:15px;line-height:1.8}.hero-actions{display:flex;align-items:center;gap:10px;margin-top:30px}.start-button{height:46px;padding:0 20px}.warning-note{max-width:520px;margin-top:28px;padding:13px 15px;display:flex;align-items:flex-start;gap:11px;border-left:2px solid var(--gold-300);border-radius:0 9px 9px 0;background:rgba(219,185,95,.055);color:var(--gold-300)}.warning-note div{display:flex;flex-direction:column;gap:4px}.warning-note strong{font-size:11px}.warning-note span{color:var(--text-muted);font-size:10px;line-height:1.55}
.save-preview-wrap{position:relative;display:grid;place-items:center}.crystal-orbit{position:absolute;border:1px solid rgba(70,219,231,.08);border-radius:50%;pointer-events:none}.orbit-one{width:620px;height:620px}.orbit-two{width:510px;height:510px;border-style:dashed;transform:rotate(18deg)}
.save-preview{position:relative;width:min(100%,560px);overflow:hidden;box-shadow:0 32px 80px rgba(0,0,0,.35),0 0 60px rgba(24,197,216,.06)}.save-preview:before{content:"";position:absolute;inset:0 0 auto;height:2px;background:linear-gradient(90deg,transparent,var(--cyan-400),transparent);opacity:.7}.preview-top{padding:18px 20px 14px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border-subtle)}.save-title-row{display:flex;align-items:center;gap:13px;padding:19px 20px 15px}.save-icon{width:50px;height:50px;display:grid;place-items:center;border:1px solid rgba(55,218,231,.23);border-radius:13px;background:linear-gradient(145deg,rgba(32,202,219,.18),rgba(12,93,112,.08));color:var(--cyan-300)}.save-title-row h2{margin:0;color:var(--text-strong);font-size:17px}.save-title-row p{margin:6px 0 0;color:var(--text-muted);font-size:11px}.path-box{margin:0 20px;padding:11px 12px;border:1px solid var(--border-subtle);border-radius:9px;background:rgba(3,12,21,.55)}.path-box span{display:block;margin-bottom:6px;color:var(--text-faint);font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.08em}.path-box code{display:block;overflow:hidden;color:#a8c0ca;font-family:"Cascadia Code",Consolas,monospace;font-size:9px;white-space:nowrap;text-overflow:ellipsis}.save-meta{display:grid;grid-template-columns:1fr 1fr;margin:17px 20px 0}.save-meta>div{padding:0 12px}.save-meta>div+div{border-left:1px solid var(--border-subtle)}.save-meta dt{color:var(--text-faint);font-size:9px;text-transform:uppercase;letter-spacing:.08em}.save-meta dd{margin:7px 0 0;display:flex;align-items:center;gap:6px;color:var(--text);font-size:11px}.save-meta dd :deep(svg){color:var(--green-300)}.safety-row{display:flex;align-items:flex-start;gap:12px;margin:18px 20px 0;padding:13px;border:1px solid rgba(47,199,215,.14);border-radius:10px;background:rgba(21,148,166,.055)}.shield-badge{color:var(--cyan-300)}.safety-row strong{font-size:11px;color:var(--text-strong)}.safety-row p{margin:4px 0 0;color:var(--text-muted);font-size:10px;line-height:1.55}.preview-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:18px;padding:15px 20px 19px;border-top:1px solid var(--border-subtle)}
.trust-strip{position:relative;z-index:3;min-height:120px;max-width:1480px;margin:0 auto;padding:20px 64px;display:grid;grid-template-columns:1fr 1.15fr auto;align-items:center;gap:40px;border-top:1px solid var(--border-subtle)}.trust-strip>div:not(.build-stamp){display:flex;align-items:center;gap:12px}.trust-icon{width:36px;height:36px;display:grid;place-items:center;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft);color:var(--cyan-300)}.trust-strip section strong{color:var(--text-strong);font-size:11px}.trust-strip section p{margin:4px 0 0;color:var(--text-faint);font-size:10px}.build-stamp{display:flex;flex-direction:column;align-items:flex-end;color:var(--text-muted);font-size:10px}.build-stamp small{margin-top:4px;color:var(--text-faint);font-size:9px}
@media(max-width:1366px){.start-header{height:72px;padding:0 36px}.start-main{min-height:calc(100vh - 170px);padding:32px 46px 28px;grid-template-columns:.88fr 1fr;gap:48px}.hero-copy h1{font-size:40px}.hero-intro{font-size:13px}.warning-note{margin-top:20px}.trust-strip{min-height:98px;padding:14px 46px}.save-title-row{padding-top:15px}.safety-row{margin-top:14px}.preview-actions{margin-top:14px}.orbit-one{width:530px;height:530px}.orbit-two{width:440px;height:440px}}
@media(max-height:760px){.start-main{padding-top:24px;padding-bottom:20px}.save-preview{transform:scale(.94)}.hero-copy h1{margin-top:12px;margin-bottom:14px}.hero-actions{margin-top:20px}.warning-note{margin-top:16px}.trust-strip{min-height:90px}}
</style>
