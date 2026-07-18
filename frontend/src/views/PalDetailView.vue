<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import AppShell from '@/components/AppShell.vue'
import EditorSection from '@/components/EditorSection.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import StatusPill from '@/components/StatusPill.vue'
import { messages } from '@/i18n/messages'
import { mockPals, mockSave } from '@/mocks/session'
import { usePrototypeStore } from '@/stores/prototype'

type TabKey = 'base' | 'stats' | 'work' | 'passives' | 'actives' | 'advanced'

const route = useRoute()
const store = usePrototypeStore()
const copy = computed(() => messages[store.locale])
const pal = computed(() => mockPals.find((item) => item.id === route.params.id) || mockPals[0])
const activeTab = ref<TabKey>('base')
const saveOpen = ref(false)
const deleteOpen = ref(false)
const nickname = ref('Stellar')
const level = ref(80)
const exp = ref(18420537)
const condensation = ref(4)
const soul = ref(30)
const iv = ref({ hp: 100, attack: 98, defense: 100 })
const work = ref({ handiwork: 1, mining: 2, transport: 3, gathering: 2, medicine: 0 })
const flags = ref({ lucky: false, boss: false, awakening: true, unknown: true })

const tabs = computed(() => [
  { key: 'base' as const, label: copy.value.pal.tabs.base },
  { key: 'stats' as const, label: copy.value.pal.tabs.stats },
  { key: 'work' as const, label: copy.value.pal.tabs.work },
  { key: 'passives' as const, label: copy.value.pal.tabs.passives },
  { key: 'actives' as const, label: copy.value.pal.tabs.actives },
  { key: 'advanced' as const, label: copy.value.pal.tabs.advanced },
])

const targetPath = computed(() => `${mockSave.path}\\Level.sav`)

function changed() {
  store.markDirty()
}

function confirmSave() {
  store.saveDraft()
  saveOpen.value = false
}
</script>

<template>
  <AppShell :eyebrow="copy.pal.collection" :title="pal.name[store.locale]">
    <RouterLink to="/dashboard" class="back-link"><AppIcon name="arrow-left" :size="15" />{{ copy.pal.back }}</RouterLink>

    <section class="pal-hero">
      <div class="pal-portrait"><div class="portrait-glow"></div><img :src="pal.icon" :alt="pal.name[store.locale]" /><span class="level-badge">Lv. {{ level }}</span></div>
      <div class="pal-title">
        <div class="pal-labels"><StatusPill tone="cyan">No. 149</StatusPill><StatusPill tone="gold">{{ copy.pal.partner }}</StatusPill></div>
        <h2>{{ pal.name[store.locale] }}<small>{{ pal.id }}</small></h2>
        <p>{{ pal.element[store.locale] }}<span></span>{{ copy.pal.ownedBy }} {{ pal.owner }}<span></span>{{ copy.pal.female }}</p>
      </div>
      <div class="draft-status" :class="{ dirty: store.dirty }"><span><AppIcon :name="store.dirty ? 'alert' : 'check'" :size="16" /></span><div><strong>{{ store.dirty ? copy.pal.unsaved : copy.pal.saved }}</strong><p>{{ copy.pal.draftHint }}</p></div></div>
      <div class="hero-actions">
        <button class="button secondary" type="button" @click="changed"><AppIcon name="copy" :size="16" />{{ copy.pal.duplicate }}</button>
        <button class="button primary" type="button" :disabled="!store.dirty" @click="saveOpen = true"><AppIcon name="save" :size="16" />{{ copy.common.save }}</button>
      </div>
    </section>

    <div class="editor-grid">
      <section class="panel editor-panel">
        <nav class="tabs" aria-label="Pal editor sections">
          <button v-for="tab in tabs" :key="tab.key" type="button" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">{{ tab.label }}</button>
        </nav>

        <div class="tab-content">
          <template v-if="activeTab === 'base'">
            <EditorSection :title="copy.pal.identity" icon="paw">
              <div class="form-grid two-column">
                <label><span class="field-label">{{ copy.pal.species }}</span><select class="field-select" @change="changed"><option>{{ pal.name[store.locale] }} · {{ pal.id }}</option><option>{{ mockPals[1].name[store.locale] }} · {{ mockPals[1].id }}</option></select></label>
                <label><span class="field-label">{{ copy.pal.nickname }}</span><input v-model="nickname" class="field-input" @input="changed" /></label>
                <label><span class="field-label">{{ copy.pal.gender }}</span><select class="field-select" @change="changed"><option>{{ copy.pal.female }}</option><option>{{ store.locale === 'zh-CN' ? '雄性' : 'Male' }}</option></select></label>
                <label><span class="field-label">{{ copy.pal.owner }}</span><select class="field-select" @change="changed"><option>Ray · 00000000-0000-0000-0000-000000000001</option><option>Mori · 00000000-0000-0000-0000-000000000002</option></select></label>
              </div>
            </EditorSection>
            <EditorSection :title="copy.pal.progression" icon="spark">
              <div class="form-grid progression-grid">
                <label><span class="field-label">{{ copy.pal.level }}</span><input v-model.number="level" class="field-input" type="number" min="1" max="80" @input="changed" /></label>
                <label><span class="field-label">{{ copy.pal.exp }}</span><input v-model.number="exp" class="field-input" type="number" @input="changed" /></label>
                <label><span class="field-label">{{ copy.pal.condensation }}</span><select v-model.number="condensation" class="field-select" @change="changed"><option v-for="rank in 5" :key="rank - 1" :value="rank - 1">{{ rank - 1 }} / 4</option></select></label>
                <label><span class="field-label">{{ copy.pal.soul }}</span><input v-model.number="soul" class="field-input" type="number" min="0" max="30" @input="changed" /></label>
              </div>
            </EditorSection>
          </template>

          <template v-else-if="activeTab === 'stats'">
            <EditorSection :title="copy.pal.ivTitle" icon="spark">
              <div class="iv-grid">
                <label v-for="key in (['hp','attack','defense'] as const)" :key="key">
                  <div><span>{{ copy.pal[key] }}</span><strong>{{ iv[key] }}<small>/ 100</small></strong></div>
                  <input v-model.number="iv[key]" type="range" min="0" max="100" @input="changed" />
                  <span v-if="iv[key] === 100" class="max-label">{{ copy.pal.max }}</span>
                </label>
              </div>
            </EditorSection>
            <div class="stat-preview">
              <div><span>{{ copy.pal.hp }}</span><strong>6,842</strong><small>+42%</small></div>
              <div><span>{{ copy.pal.attack }}</span><strong>1,936</strong><small>+38%</small></div>
              <div><span>{{ copy.pal.defense }}</span><strong>2,104</strong><small>+41%</small></div>
            </div>
          </template>

          <template v-else-if="activeTab === 'work'">
            <EditorSection :title="copy.pal.workTitle" :hint="copy.pal.workHint" icon="settings">
              <div class="work-grid">
                <label v-for="key in (['handiwork','mining','transport','gathering','medicine'] as const)" :key="key"><span>{{ copy.pal[key] }}</span><div class="stepper"><button type="button" @click="work[key] = Math.max(0, work[key]-1); changed()">−</button><strong :class="{ boosted: work[key] > 4 }">{{ work[key] }}</strong><button type="button" @click="work[key] = Math.min(5, work[key]+1); changed()">+</button></div></label>
              </div>
            </EditorSection>
          </template>

          <template v-else-if="activeTab === 'passives'">
            <EditorSection :title="copy.pal.passivesTitle" :hint="copy.pal.passivesHint" icon="spark">
              <div class="skill-list">
                <div v-for="(name, index) in copy.pal.passiveNames" :key="name" class="skill-row"><span class="skill-rating">{{ index < 2 ? 'III' : 'II' }}</span><div><strong>{{ name }}</strong><p>{{ store.locale === 'zh-CN' ? ['攻击与防御提升 20%','受到的伤害降低 15%','移动速度提升 30%','工作速度提升 50%'][index] : ['Attack and defense +20%','Damage received -15%','Movement speed +30%','Work speed +50%'][index] }}</p></div><button type="button" @click="changed">×</button></div>
                <button class="add-skill" type="button" @click="changed">+ {{ copy.pal.addSkill }}</button>
              </div>
            </EditorSection>
          </template>

          <template v-else-if="activeTab === 'actives'">
            <EditorSection :title="copy.pal.activeTitle" icon="spark">
              <div class="active-list">
                <div v-for="(name, index) in copy.pal.activeNames" :key="name"><span class="element-gem" :class="`gem-${index}`"></span><section><strong>{{ name }}</strong><p>{{ index === 0 ? 'Dark' : index === 1 ? 'Dragon' : 'Dark' }}</p></section><dl><div><dt>{{ copy.pal.power }}</dt><dd>{{ [160, 100, 120][index] }}</dd></div><div><dt>{{ copy.pal.cooldown }}</dt><dd>{{ [45, 15, 30][index] }}s</dd></div></dl><button type="button" @click="changed">×</button></div>
              </div>
            </EditorSection>
          </template>

          <template v-else>
            <EditorSection :title="copy.pal.advancedTitle" :hint="copy.pal.advancedHint" icon="settings">
              <div class="toggle-list">
                <label v-for="key in (['lucky','boss','awakening','unknown'] as const)" :key="key"><div><strong>{{ copy.pal[key] }}</strong><p>{{ key === 'unknown' ? (store.locale === 'zh-CN' ? '写回时原样保留解析器未识别的属性' : 'Keep parser-unknown properties unchanged') : (store.locale === 'zh-CN' ? '布尔型存档标记' : 'Boolean save flag') }}</p></div><input v-model="flags[key]" type="checkbox" @change="changed" /><span class="toggle"></span></label>
              </div>
            </EditorSection>
            <div class="danger-zone"><div><strong>{{ copy.pal.dangerTitle }}</strong><p>{{ copy.pal.dangerCopy }}</p></div><button class="button danger" type="button" @click="deleteOpen = true"><AppIcon name="trash" :size="16" />{{ copy.pal.remove }}</button></div>
          </template>
        </div>
      </section>

      <aside class="summary-column">
        <article class="panel summary-panel">
          <div class="panel-header"><h2>{{ copy.pal.summary }}</h2><StatusPill tone="green" dot>{{ copy.pal.valid }}</StatusPill></div>
          <dl class="summary-list">
            <div><dt>{{ copy.pal.location }}</dt><dd>{{ copy.pal.palbox }}</dd></div>
            <div><dt>{{ copy.pal.level }}</dt><dd>{{ level }} / 80</dd></div>
            <div><dt>{{ copy.pal.condensation }}</dt><dd><span class="stars">★★★★</span> {{ condensation }} / 4</dd></div>
            <div><dt>{{ copy.pal.passivesCount }}</dt><dd>4 / 4</dd></div>
            <div><dt>{{ copy.pal.activesCount }}</dt><dd>3 / 3</dd></div>
            <div><dt>{{ copy.pal.integrity }}</dt><dd class="valid"><AppIcon name="shield" :size="15" />{{ copy.pal.valid }}</dd></div>
          </dl>
        </article>
        <article class="draft-card" :class="{ dirty: store.dirty }"><span><AppIcon :name="store.dirty ? 'alert' : 'shield'" /></span><div><strong>{{ store.dirty ? copy.pal.unsaved : copy.pal.saved }}</strong><p>{{ copy.pal.draftHint }}</p></div></article>
      </aside>
    </div>

    <ModalDialog :open="saveOpen" :title="copy.pal.saveConfirmTitle" width="620px" @close="saveOpen = false">
      <p class="confirm-copy">{{ copy.pal.saveConfirmCopy }}</p>
      <div class="path-confirm"><span>{{ copy.pal.targetPath }}</span><code>{{ targetPath }}</code></div>
      <div class="path-confirm backup"><span>{{ copy.pal.backupPath }}</span><code>{{ mockSave.backupPath }}</code></div>
      <template #footer><button class="button secondary" type="button" @click="saveOpen = false">{{ copy.common.cancel }}</button><button class="button primary" type="button" @click="confirmSave"><AppIcon name="shield" :size="16" />{{ copy.common.confirm }}</button></template>
    </ModalDialog>

    <ModalDialog :open="deleteOpen" :title="copy.pal.deleteConfirmTitle" width="520px" @close="deleteOpen = false">
      <div class="delete-copy"><span><AppIcon name="alert" /></span><p>{{ copy.pal.deleteConfirmCopy }}</p></div>
      <template #footer><button class="button secondary" type="button" @click="deleteOpen = false">{{ copy.common.cancel }}</button><button class="button danger" type="button" @click="changed(); deleteOpen = false"><AppIcon name="trash" :size="16" />{{ copy.pal.remove }}</button></template>
    </ModalDialog>
  </AppShell>
</template>

<style scoped>
.back-link{display:inline-flex;align-items:center;gap:7px;margin-bottom:13px;color:var(--text-muted);font-size:10px;text-decoration:none}.back-link:hover{color:var(--cyan-300)}
.pal-hero{min-height:112px;padding:14px 16px;display:flex;align-items:center;gap:16px;border:1px solid var(--border-subtle);border-radius:16px;background:linear-gradient(105deg,rgba(15,37,56,.92),rgba(8,22,36,.78));box-shadow:var(--shadow-card)}.pal-portrait{position:relative;width:84px;height:84px;flex:0 0 84px;display:grid;place-items:center;border:1px solid rgba(63,217,229,.18);border-radius:14px;background:radial-gradient(circle at 50% 35%,rgba(62,216,226,.2),rgba(7,21,34,.85));overflow:hidden}.portrait-glow{position:absolute;width:58px;height:58px;border-radius:50%;background:rgba(52,212,225,.18);filter:blur(18px)}.pal-portrait img{position:relative;width:80px;height:80px;object-fit:contain;filter:drop-shadow(0 8px 10px rgba(0,0,0,.5))}.level-badge{position:absolute;right:5px;bottom:5px;padding:3px 6px;border-radius:5px;background:rgba(3,10,17,.88);color:var(--gold-200);font-size:8px;font-weight:750}.pal-title{min-width:220px}.pal-labels{display:flex;gap:6px;margin-bottom:8px}.pal-title h2{margin:0;color:var(--text-strong);font-size:22px;letter-spacing:-.03em}.pal-title h2 small{margin-left:9px;color:var(--text-faint);font-size:9px;font-family:"Cascadia Code",monospace;font-weight:500;letter-spacing:0}.pal-title p{display:flex;align-items:center;gap:8px;margin:7px 0 0;color:var(--text-muted);font-size:10px}.pal-title p span{width:3px;height:3px;border-radius:50%;background:var(--text-faint)}.draft-status{margin-left:auto;display:flex;align-items:center;gap:9px;padding:9px 11px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft)}.draft-status>span{color:var(--green-300)}.draft-status.dirty{border-color:rgba(220,183,92,.22);background:rgba(220,183,92,.06)}.draft-status.dirty>span{color:var(--gold-300)}.draft-status strong{display:block;color:var(--text);font-size:9px}.draft-status p{margin:3px 0 0;color:var(--text-faint);font-size:7px}.hero-actions{display:flex;gap:8px}.hero-actions .button:disabled{opacity:.42;cursor:default;filter:saturate(.5)}.hero-actions .button:disabled:hover{transform:none}
.editor-grid{display:grid;grid-template-columns:minmax(0,1fr) 270px;gap:16px;margin-top:16px}.editor-panel{overflow:hidden;min-height:500px}.tabs{padding:0 14px;display:flex;align-items:center;gap:3px;border-bottom:1px solid var(--border-subtle);overflow-x:auto}.tabs button{position:relative;height:52px;padding:0 13px;border:0;background:transparent;color:var(--text-muted);font-size:10px;font-weight:680;white-space:nowrap;cursor:pointer}.tabs button:hover{color:var(--text)}.tabs button.active{color:var(--cyan-200)}.tabs button.active:after{content:"";position:absolute;left:12px;right:12px;bottom:-1px;height:2px;border-radius:2px 2px 0 0;background:var(--cyan-400);box-shadow:0 0 10px rgba(35,199,216,.42)}.tab-content{padding:19px 20px}.section-block+.section-block{margin-top:22px}.form-grid{display:grid;gap:13px}.two-column{grid-template-columns:1fr 1fr}.progression-grid{grid-template-columns:.7fr 1.2fr .85fr .75fr}
.iv-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:13px}.iv-grid label{position:relative;padding:15px;border:1px solid var(--border-subtle);border-radius:12px;background:var(--surface-soft)}.iv-grid label>div{display:flex;align-items:baseline;justify-content:space-between;color:var(--text-muted);font-size:10px}.iv-grid strong{color:var(--text-strong);font-size:20px}.iv-grid strong small{color:var(--text-faint);font-size:8px}.iv-grid input{width:100%;height:3px;margin-top:18px;accent-color:var(--cyan-400)}.max-label{position:absolute;right:14px;bottom:8px;color:var(--gold-300);font-size:7px;text-transform:uppercase}.stat-preview{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px}.stat-preview>div{padding:16px;border:1px solid var(--border-subtle);border-radius:12px;background:rgba(5,16,27,.45)}.stat-preview span{display:block;color:var(--text-faint);font-size:9px}.stat-preview strong{display:block;margin-top:8px;color:var(--text-strong);font-size:22px}.stat-preview small{color:var(--green-300);font-size:8px}
.work-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.work-grid label{min-height:58px;padding:10px 12px;display:flex;align-items:center;justify-content:space-between;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft);color:var(--text);font-size:10px}.stepper{height:30px;display:flex;align-items:center;border:1px solid var(--border-subtle);border-radius:8px;overflow:hidden}.stepper button{width:28px;height:100%;border:0;background:rgba(255,255,255,.035);color:var(--text-muted);cursor:pointer}.stepper button:hover{color:var(--cyan-300);background:var(--surface-hover)}.stepper strong{width:30px;text-align:center;color:var(--text-strong);font-size:11px}.stepper strong.boosted{color:var(--gold-300)}
.skill-list,.active-list{display:flex;flex-direction:column;gap:8px}.skill-row{min-height:62px;padding:10px 12px;display:grid;grid-template-columns:36px 1fr 28px;align-items:center;gap:11px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft)}.skill-rating{width:34px;height:34px;display:grid;place-items:center;border-radius:9px;background:rgba(220,183,92,.09);color:var(--gold-300);font-size:9px;font-weight:800}.skill-row strong,.active-list strong{color:var(--text-strong);font-size:10px}.skill-row p,.active-list p{margin:4px 0 0;color:var(--text-faint);font-size:8px}.skill-row button,.active-list>div>button{width:26px;height:26px;border:0;border-radius:7px;background:transparent;color:var(--text-faint);cursor:pointer}.skill-row button:hover,.active-list>div>button:hover{background:rgba(217,78,92,.1);color:var(--red-300)}.add-skill{height:38px;border:1px dashed var(--border-subtle);border-radius:9px;background:transparent;color:var(--cyan-300);font-size:10px;cursor:pointer}.add-skill:hover{border-color:var(--border-bright);background:var(--surface-hover)}
.active-list>div{min-height:66px;padding:10px 12px;display:grid;grid-template-columns:34px 1fr auto 26px;align-items:center;gap:11px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft)}.element-gem{width:30px;height:30px;border-radius:9px;background:radial-gradient(circle at 35% 30%,#a7fbff,#168fa6 65%,#0e5267);box-shadow:inset 0 0 0 1px rgba(255,255,255,.16)}.gem-1{background:radial-gradient(circle at 35% 30%,#f6b6ff,#8056df 65%,#382773)}.gem-2{background:radial-gradient(circle at 35% 30%,#b9a9ee,#47366e 65%,#241b3a)}.active-list dl{display:flex;gap:18px;margin:0}.active-list dl div{text-align:right}.active-list dt{color:var(--text-faint);font-size:7px;text-transform:uppercase}.active-list dd{margin:4px 0 0;color:var(--text);font-size:9px}
.toggle-list{border:1px solid var(--border-subtle);border-radius:11px;overflow:hidden}.toggle-list label{position:relative;min-height:64px;padding:11px 14px;display:flex;align-items:center;border-bottom:1px solid var(--border-subtle);cursor:pointer}.toggle-list label:last-child{border:0}.toggle-list label>div{flex:1}.toggle-list strong{color:var(--text);font-size:10px}.toggle-list p{margin:4px 0 0;color:var(--text-faint);font-size:8px}.toggle-list input{position:absolute;opacity:0}.toggle{position:relative;width:36px;height:20px;border-radius:20px;background:#203542;transition:.18s}.toggle:after{content:"";position:absolute;width:14px;height:14px;left:3px;top:3px;border-radius:50%;background:#8197a1;transition:.18s}.toggle-list input:checked+.toggle{background:rgba(25,185,204,.38);box-shadow:inset 0 0 0 1px rgba(56,223,234,.3)}.toggle-list input:checked+.toggle:after{left:19px;background:var(--cyan-200);box-shadow:0 0 8px rgba(76,225,236,.4)}.danger-zone{margin-top:18px;padding:14px 15px;display:flex;align-items:center;justify-content:space-between;gap:20px;border:1px solid rgba(217,78,92,.2);border-radius:11px;background:rgba(217,78,92,.045)}.danger-zone strong{color:#ff9ba4;font-size:10px}.danger-zone p{margin:5px 0 0;color:#9d7479;font-size:8px;line-height:1.5}
.summary-column{display:flex;flex-direction:column;gap:13px}.summary-panel{overflow:hidden}.summary-panel .panel-header{padding:15px}.summary-list{margin:0;padding:3px 15px 10px}.summary-list>div{min-height:51px;display:flex;align-items:center;justify-content:space-between;gap:12px;border-bottom:1px solid var(--border-subtle)}.summary-list>div:last-child{border:0}.summary-list dt{color:var(--text-faint);font-size:8px}.summary-list dd{margin:0;color:var(--text);font-size:9px;text-align:right}.stars{color:var(--gold-300);letter-spacing:1px}.summary-list dd.valid{display:flex;align-items:center;gap:5px;color:var(--green-300)}.draft-card{padding:14px;display:flex;align-items:flex-start;gap:10px;border:1px solid rgba(82,211,158,.18);border-radius:12px;background:rgba(82,211,158,.055)}.draft-card>span{color:var(--green-300)}.draft-card.dirty{border-color:rgba(220,183,92,.2);background:rgba(220,183,92,.055)}.draft-card.dirty>span{color:var(--gold-300)}.draft-card strong{font-size:10px;color:var(--text)}.draft-card p{margin:4px 0 0;color:var(--text-faint);font-size:8px}
.confirm-copy{margin:0 0 16px;color:var(--text-muted);font-size:11px;line-height:1.6}.path-confirm{padding:12px;border:1px solid var(--border-subtle);border-radius:10px;background:rgba(3,12,21,.55)}.path-confirm+.path-confirm{margin-top:10px}.path-confirm span{display:block;margin-bottom:7px;color:var(--text-faint);font-size:8px;font-weight:700;text-transform:uppercase;letter-spacing:.08em}.path-confirm code{display:block;overflow:hidden;color:#a7bdc6;font-size:9px;white-space:nowrap;text-overflow:ellipsis}.path-confirm.backup{border-color:rgba(85,211,157,.14)}.delete-copy{display:flex;align-items:flex-start;gap:12px;padding:14px;border:1px solid rgba(217,78,92,.18);border-radius:10px;background:rgba(217,78,92,.055)}.delete-copy span{color:var(--red-300)}.delete-copy p{margin:0;color:var(--text-muted);font-size:11px;line-height:1.6}
@media(max-width:1366px){.pal-hero{min-height:98px}.pal-portrait{width:72px;height:72px;flex-basis:72px}.pal-portrait img{width:70px;height:70px}.pal-title h2{font-size:19px}.draft-status{display:none}.editor-grid{grid-template-columns:minmax(0,1fr) 248px}.tabs button{padding:0 10px}.tab-content{padding:16px}.progression-grid{grid-template-columns:.65fr 1.1fr .8fr .7fr}}
@media(max-height:760px){.back-link{margin-bottom:8px}.pal-hero{min-height:86px;padding:9px 13px}.pal-portrait{width:66px;height:66px;flex-basis:66px}.pal-portrait img{width:64px;height:64px}.editor-grid{margin-top:12px}.editor-panel{min-height:430px}.tabs button{height:44px}.tab-content{padding-top:14px}.summary-list>div{min-height:45px}}
</style>
