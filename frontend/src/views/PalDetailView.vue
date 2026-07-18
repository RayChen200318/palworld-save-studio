<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import AppShell from '@/components/AppShell.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import StatusPill from '@/components/StatusPill.vue'
import { messages } from '@/i18n/messages'
import { apiClient } from '@/services/apiClient'
import { useCatalogStore } from '@/stores/catalog'
import { useCollectionStore } from '@/stores/collection'
import { useDraftStore } from '@/stores/draft'
import { useSessionStore } from '@/stores/session'
import type { PalDetail } from '@/types/domain'

type Tab = 'base' | 'stats' | 'work' | 'passives' | 'actives' | 'advanced'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const catalog = useCatalogStore()
const collection = useCollectionStore()
const draft = useDraftStore()
const copy = computed(() => messages[session.locale])
const form = ref<PalDetail | null>(null)
const activeTab = ref<Tab>('base')
const deleteOpen = ref(false)
const rawJson = ref('')
const passiveToAdd = ref('')
const activeToAdd = ref('')
const instanceId = computed(() => String(route.params.id))
const tabs = computed(() => Object.entries(copy.value.pal.tabs) as [Tab, string][])
const statFields = computed(() => [
  { key: 'Talent_HP', label: copy.value.pal.hp }, { key: 'Talent_Shot', label: copy.value.pal.attack },
  { key: 'Talent_Defense', label: copy.value.pal.defense }, { key: 'Talent_Melee', label: 'Melee IV' },
] as const)
const soulFields = computed(() => [
  { key: 'Rank_HP', label: copy.value.pal.hp }, { key: 'Rank_Attack', label: copy.value.pal.attack },
  { key: 'Rank_Defence', label: copy.value.pal.defense }, { key: 'Rank_CraftSpeed', label: copy.value.pal.workSpeed },
] as const)
const availablePassives = computed(() => catalog.passives.filter((item) => !form.value?.PassiveSkillList.includes(item.InternalName)))
const availableActives = computed(() => catalog.actives.filter((item) => !form.value?.MasteredWaza.includes(item.InternalName)))
const workKeys = computed(() => {
  if (!form.value) return []
  const species = catalog.palById.get(form.value.SpeciesKey) || catalog.palById.get(form.value.CharacterID)
  return [...new Set([...Object.keys(species?.Suitabilities || {}), ...Object.keys(form.value.Suitabilities)])]
    .filter((key) => (species?.Suitabilities[key] || form.value?.Suitabilities[key] || 0) > 0)
})

function clone<T>(value: T): T { return JSON.parse(JSON.stringify(value)) as T }

async function load() {
  await session.bootstrap()
  if (!session.loaded) {
    router.replace('/')
    return
  }
  await Promise.all([catalog.load(), collection.loadPals(), collection.loadPlayers()])
  const pal = await collection.loadPal(instanceId.value)
  form.value = clone(pal)
  rawJson.value = ''
}

async function apply(changes: Partial<PalDetail>) {
  const updated = await collection.patchPal(instanceId.value, changes)
  form.value = clone(updated)
}

function stringChange(key: 'NickName', event: Event) {
  apply({ [key]: (event.target as HTMLInputElement).value })
}

function numberChange(key: keyof PalDetail, event: Event) {
  apply({ [key]: Number((event.target as HTMLInputElement).value) } as Partial<PalDetail>)
}

function selectChange(key: keyof PalDetail, event: Event) {
  apply({ [key]: (event.target as HTMLSelectElement).value } as Partial<PalDetail>)
}

async function addPassive() {
  if (!form.value || !passiveToAdd.value) return
  await apply({ PassiveSkillList: [...form.value.PassiveSkillList, passiveToAdd.value] })
  passiveToAdd.value = ''
}

function removePassive(skill: string) {
  if (!form.value) return
  apply({ PassiveSkillList: form.value.PassiveSkillList.filter((item) => item !== skill) })
}

async function addMastered() {
  if (!form.value || !activeToAdd.value) return
  await apply({ MasteredWaza: [...form.value.MasteredWaza, activeToAdd.value] })
  activeToAdd.value = ''
}

function equip(skill: string) {
  if (!form.value || form.value.EquipWaza.length >= 3) return
  apply({ EquipWaza: [...form.value.EquipWaza, skill] })
}

function unequip(skill: string) {
  if (!form.value) return
  apply({ EquipWaza: form.value.EquipWaza.filter((item) => item !== skill) })
}

function forget(skill: string) {
  if (!form.value) return
  apply({
    MasteredWaza: form.value.MasteredWaza.filter((item) => item !== skill),
    EquipWaza: form.value.EquipWaza.filter((item) => item !== skill),
  })
}

function toggle(key: 'IsBOSS' | 'IsRarePal' | 'IsTower' | 'IsAwakening', event: Event) {
  apply({ [key]: (event.target as HTMLInputElement).checked })
}

async function duplicate() {
  const pal = await collection.duplicatePal(instanceId.value)
  router.push(`/pals/${pal.InstanceId}`)
}

async function remove() {
  await collection.deletePal(instanceId.value)
  deleteOpen.value = false
  router.push('/pals')
}

async function retrieve() {
  await collection.retrievePal(instanceId.value)
  if (collection.selectedPal) form.value = clone(collection.selectedPal)
}

async function loadRaw() {
  rawJson.value = await apiClient.getRawPal(instanceId.value)
}

async function exportRaw() {
  if (!rawJson.value) await loadRaw()
  const blob = new Blob([rawJson.value], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${instanceId.value}.json`
  link.click()
  URL.revokeObjectURL(url)
}

function workLabel(key: string) { return key.replace('EPalWorkSuitability::', '') }
function passiveName(key: string) { return catalog.passiveById.get(key)?.I18n[0] || key }
function activeName(key: string) { return catalog.activeById.get(key)?.I18n[0] || key }

onMounted(load)
watch(instanceId, load)
</script>

<template>
  <AppShell :eyebrow="copy.pal.eyebrow" :title="form?.SpeciesName || copy.common.loading">
    <div v-if="!form" class="loading"><AppIcon name="refresh" />{{ copy.common.loading }}</div>
    <template v-else>
      <RouterLink to="/pals" class="back-link"><AppIcon name="arrow-left" :size="15" />{{ copy.pal.back }}</RouterLink>
      <section class="pal-hero panel">
        <div class="pal-portrait"><img :src="`/image/pals/${form.IconAccessKey}`" alt="" /></div>
        <div class="pal-title"><div><StatusPill :tone="form.ObjectType === 'human' ? 'gold' : 'cyan'">{{ form.ObjectType === 'human' ? copy.pals.typeHuman : copy.pals.typePal }}</StatusPill><StatusPill v-if="form.IsAnomalous" tone="red">{{ copy.pals.anomalous }}</StatusPill></div><h2>{{ form.SpeciesName }}</h2><p>{{ form.NickName || form.CharacterID }} · {{ copy.pal.ownedBy }} {{ form.OwnerName || copy.common.none }}</p></div>
        <div class="hero-actions"><button class="button secondary" type="button" :disabled="draft.pending" @click="duplicate"><AppIcon name="copy" :size="16" />{{ copy.pal.duplicate }}</button><button class="button danger" type="button" @click="deleteOpen = true"><AppIcon name="trash" :size="16" />{{ copy.pal.remove }}</button></div>
      </section>

      <section class="editor-grid">
        <article class="panel editor-panel">
          <nav class="tabs"><button v-for="[key, label] in tabs" :key="key" type="button" :class="{ active: activeTab === key }" @click="activeTab = key">{{ label }}</button></nav>
          <div class="tab-content">
            <template v-if="activeTab === 'base'">
              <section class="editor-section"><div class="section-heading"><h3>{{ copy.pal.identity }}</h3></div><div class="form-grid three"><label><span class="field-label">{{ copy.pal.species }}</span><select class="field-select" :value="form.CharacterID" @change="selectChange('CharacterID', $event)"><option v-for="item in catalog.pals" :key="item.InternalName" :value="item.InternalName">{{ item.I18n }} · {{ item.InternalName }}</option></select></label><label><span class="field-label">{{ copy.pal.nickname }}</span><input class="field-input" :value="form.NickName" maxlength="64" @blur="stringChange('NickName', $event)" /></label><label><span class="field-label">{{ copy.pal.gender }}</span><select class="field-select" :value="form.Gender || ''" :disabled="form.IsHuman" @change="selectChange('Gender', $event)"><option value="EPalGenderType::Male">{{ copy.pal.male }}</option><option value="EPalGenderType::Female">{{ copy.pal.female }}</option></select></label></div></section>
              <section class="editor-section"><div class="section-heading"><h3>{{ copy.pal.progression }}</h3></div><div class="form-grid three"><label><span class="field-label">{{ copy.common.level }}</span><input class="field-input" type="number" min="1" max="80" :value="form.Level" @blur="numberChange('Level', $event)" /></label><label><span class="field-label">{{ copy.pal.friendship }}</span><input class="field-input" type="number" min="-3" max="10" :value="form.FriendshipLevel" @blur="numberChange('FriendshipLevel', $event)" /></label><label><span class="field-label">{{ copy.pal.condensation }}</span><select class="field-select" :value="form.Rank" @change="numberChange('Rank', $event)"><option v-for="rank in 5" :key="rank" :value="rank">{{ rank - 1 }} ★</option></select></label></div></section>
              <section class="editor-section"><div class="section-heading"><h3>{{ copy.pal.computed }}</h3></div><div class="stat-cards"><div><span>{{ copy.pal.hp }}</span><strong>{{ form.ComputedMaxHP ?? '—' }}</strong></div><div><span>{{ copy.pal.attack }}</span><strong>{{ form.ComputedAttack ?? '—' }}</strong></div><div><span>{{ copy.pal.defense }}</span><strong>{{ form.ComputedDefense ?? '—' }}</strong></div><div><span>{{ copy.pal.workSpeed }}</span><strong>{{ form.ComputedCraftSpeed ?? '—' }}</strong></div></div></section>
            </template>

            <template v-else-if="activeTab === 'stats'">
              <section class="editor-section"><div class="section-heading"><h3>{{ copy.pal.iv }}</h3></div><div class="range-grid"><label v-for="field in statFields" :key="field.key"><div><span>{{ field.label }}</span><strong>{{ form[field.key] }}</strong></div><input type="range" min="0" max="100" :value="form[field.key]" @change="numberChange(field.key, $event)" /></label></div></section>
              <section class="editor-section"><div class="section-heading"><h3>{{ copy.pal.soul }}</h3></div><div class="range-grid"><label v-for="field in soulFields" :key="field.key"><div><span>{{ field.label }}</span><strong>{{ form[field.key] }} / 20</strong></div><input type="range" min="0" max="20" :value="form[field.key]" @change="numberChange(field.key, $event)" /></label></div></section>
            </template>

            <template v-else-if="activeTab === 'work'">
              <section class="editor-section"><div class="section-heading"><div><h3>{{ copy.pal.workTitle }}</h3><p>{{ copy.pal.workHint }}</p></div></div><div class="work-grid"><label v-for="key in workKeys" :key="key"><span>{{ workLabel(key) }}</span><select class="field-select" :value="form.Suitabilities[key] || 0" @change="apply({ Suitabilities: { [key]: Number(($event.target as HTMLSelectElement).value) } })"><option v-for="rank in 6" :key="rank - 1" :value="rank - 1">Lv. {{ rank - 1 }}</option></select></label></div></section>
            </template>

            <template v-else-if="activeTab === 'passives'">
              <section class="editor-section"><div class="section-heading"><div><h3>{{ copy.pal.passivesTitle }}</h3><p>{{ copy.pal.passivesHint }}</p></div><StatusPill :tone="form.PassiveSkillList.length >= 4 ? 'gold' : 'cyan'">{{ form.PassiveSkillList.length }} / 4</StatusPill></div><div class="skill-list"><article v-for="skill in form.PassiveSkillList" :key="skill"><div><strong>{{ passiveName(skill) }}</strong><small>{{ skill }}</small></div><button type="button" @click="removePassive(skill)"><AppIcon name="trash" :size="15" /></button></article></div><div class="skill-add"><select v-model="passiveToAdd" class="field-select"><option value="">{{ copy.pal.addPassive }}</option><option v-for="skill in availablePassives" :key="skill.InternalName" :value="skill.InternalName">{{ skill.I18n[0] }} · {{ skill.InternalName }}</option></select><button class="button secondary" type="button" :disabled="!passiveToAdd || form.PassiveSkillList.length >= 4" @click="addPassive"><AppIcon name="plus" :size="15" />{{ copy.common.add }}</button></div></section>
            </template>

            <template v-else-if="activeTab === 'actives'">
              <section class="editor-section"><div class="section-heading"><div><h3>{{ copy.pal.activeHint }}</h3></div></div><div class="dual-skills"><div><h4>{{ copy.pal.mastered }}</h4><div class="skill-list compact"><article v-for="skill in form.MasteredWaza" :key="skill"><div><strong>{{ activeName(skill) }}</strong><small>{{ skill }}</small></div><div><button v-if="!form.EquipWaza.includes(skill)" type="button" :disabled="form.EquipWaza.length >= 3" @click="equip(skill)">{{ copy.pal.equip }}</button><button type="button" @click="forget(skill)">{{ copy.pal.forget }}</button></div></article></div><div class="skill-add"><select v-model="activeToAdd" class="field-select"><option value="">{{ copy.pal.addActive }}</option><option v-for="skill in availableActives" :key="skill.InternalName" :value="skill.InternalName">{{ skill.I18n[0] }} · {{ skill.InternalName }}</option></select><button class="button secondary" type="button" :disabled="!activeToAdd" @click="addMastered"><AppIcon name="plus" :size="15" />{{ copy.common.add }}</button></div></div><div><h4>{{ copy.pal.equipped }} · {{ form.EquipWaza.length }} / 3</h4><div class="equipped-slots"><article v-for="skill in form.EquipWaza" :key="skill"><span><strong>{{ activeName(skill) }}</strong><small>{{ skill }}</small></span><button type="button" @click="unequip(skill)">{{ copy.pal.unequip }}</button></article><article v-for="slot in (3 - form.EquipWaza.length)" :key="`empty-${slot}`" class="empty-slot">—</article></div></div></div></section>
            </template>

            <template v-else>
              <section class="editor-section"><div class="section-heading"><h3>{{ copy.pal.flags }}</h3></div><div class="flag-grid"><label><input type="checkbox" :checked="form.IsRarePal" :disabled="form.IsHuman" @change="toggle('IsRarePal', $event)" /><span>{{ copy.pal.lucky }}</span></label><label><input type="checkbox" :checked="form.IsBOSS" :disabled="form.IsHuman || !form.HasBossVariant" @change="toggle('IsBOSS', $event)" /><span>{{ copy.pal.boss }}</span></label><label><input type="checkbox" :checked="form.IsTower" :disabled="form.IsHuman || !form.HasTowerVariant" @change="toggle('IsTower', $event)" /><span>{{ copy.pal.tower }}</span></label><label><input type="checkbox" :checked="form.IsAwakening" @change="toggle('IsAwakening', $event)" /><span>{{ copy.pal.awakening }}</span></label></div></section>
              <section v-if="form.Location === 'outside'" class="editor-section retrieve"><div><h3>{{ copy.pal.retrieve }}</h3><p>{{ copy.locations.outside }} · {{ form.OwnerName || copy.common.none }}</p></div><button class="button secondary" type="button" @click="retrieve"><AppIcon name="box" :size="16" />{{ copy.pal.retrieve }}</button></section>
              <section class="editor-section"><div class="section-heading"><div><h3>{{ copy.pal.rawTitle }}</h3><p>{{ copy.pal.rawHint }}</p></div><div class="raw-actions"><button class="button secondary" type="button" @click="loadRaw"><AppIcon name="code" :size="16" />{{ copy.pal.loadRaw }}</button><button class="button secondary" type="button" @click="exportRaw"><AppIcon name="save" :size="16" />{{ copy.pal.exportRaw }}</button></div></div><textarea v-if="rawJson" class="raw-json" :value="rawJson" readonly spellcheck="false" /></section>
              <section class="danger-zone"><div><h3>{{ copy.pal.danger }}</h3><p>{{ copy.pal.dangerCopy }}</p></div><button class="button danger" type="button" @click="deleteOpen = true"><AppIcon name="trash" :size="16" />{{ copy.pal.remove }}</button></section>
            </template>
            <p v-if="draft.error" class="error-copy">{{ draft.error }}</p>
          </div>
        </article>

        <aside class="panel summary-card"><div class="summary-portrait"><img :src="`/image/pals/${form.IconAccessKey}`" alt="" /></div><h3>{{ form.SpeciesName }}</h3><p>{{ form.InstanceId }}</p><dl><div><dt>{{ copy.pal.objectType }}</dt><dd>{{ form.ObjectType === 'human' ? copy.pals.typeHuman : copy.pals.typePal }}</dd></div><div><dt>{{ copy.common.location }}</dt><dd>{{ copy.locations[form.Location] }}</dd></div><div><dt>{{ copy.common.owner }}</dt><dd>{{ form.OwnerName || copy.common.none }}</dd></div><div><dt>{{ copy.pal.passivesCount }}</dt><dd>{{ form.PassiveSkillList.length }} / 4</dd></div><div><dt>{{ copy.pal.activesCount }}</dt><dd>{{ form.EquipWaza.length }} / 3</dd></div><div><dt>{{ copy.pal.integrity }}</dt><dd class="valid"><AppIcon name="check" :size="13" />{{ copy.pal.valid }}</dd></div></dl></aside>
      </section>
    </template>

    <ModalDialog :open="deleteOpen" :title="copy.pal.deleteTitle" @close="deleteOpen = false"><p class="dialog-copy">{{ copy.pal.deleteCopy }}</p><template #footer><button class="button secondary" type="button" @click="deleteOpen = false">{{ copy.common.cancel }}</button><button class="button danger" type="button" :disabled="draft.pending" @click="remove">{{ copy.pal.remove }}</button></template></ModalDialog>
  </AppShell>
</template>

<style scoped>
.loading{height:520px;display:grid;place-items:center;align-content:center;gap:12px;color:var(--text-muted)}.loading .app-icon{animation:spin 1s linear infinite}.back-link{display:inline-flex;align-items:center;gap:7px;margin-bottom:12px;color:var(--text-muted);font-size:10px;text-decoration:none}.back-link:hover{color:var(--cyan-300)}.pal-hero{min-height:108px;padding:14px 17px;display:flex;align-items:center;gap:16px}.pal-portrait{width:78px;height:78px;display:grid;place-items:center;border:1px solid rgba(54,212,225,.2);border-radius:14px;background:radial-gradient(circle,rgba(36,195,211,.12),rgba(3,13,22,.5))}.pal-portrait img{width:74px;height:74px;object-fit:contain}.pal-title{min-width:0;flex:1}.pal-title>div{display:flex;gap:6px}.pal-title :deep(.status-pill){min-height:21px;font-size:8px}.pal-title h2{margin:8px 0 4px;color:var(--text-strong);font-size:21px}.pal-title p{margin:0;color:var(--text-muted);font-size:10px}.hero-actions{display:flex;gap:8px}.editor-grid{margin-top:14px;display:grid;grid-template-columns:minmax(0,1fr) 255px;gap:14px;align-items:start}.editor-panel{min-height:560px}.tabs{height:50px;padding:0 9px;display:flex;align-items:end;border-bottom:1px solid var(--border-subtle);overflow:auto}.tabs button{height:49px;padding:0 15px;border:0;border-bottom:2px solid transparent;background:transparent;color:var(--text-muted);font:inherit;font-size:10px;font-weight:700;white-space:nowrap;cursor:pointer}.tabs button.active{border-color:var(--cyan-400);color:var(--cyan-200)}.tab-content{padding:19px}.editor-section+.editor-section{margin-top:22px;padding-top:20px;border-top:1px solid var(--border-subtle)}.section-heading{margin-bottom:13px;display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.section-heading h3,.retrieve h3{margin:0;color:var(--text-strong);font-size:13px}.section-heading p,.retrieve p{margin:5px 0 0;color:var(--text-muted);font-size:9px;line-height:1.5}.form-grid{display:grid;gap:11px}.form-grid.three{grid-template-columns:repeat(3,1fr)}.stat-cards{display:grid;grid-template-columns:repeat(4,1fr);gap:9px}.stat-cards div{padding:13px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft)}.stat-cards span{display:block;color:var(--text-faint);font-size:8px;text-transform:uppercase}.stat-cards strong{display:block;margin-top:7px;color:var(--cyan-200);font-size:17px}.range-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.range-grid label{padding:13px;border:1px solid var(--border-subtle);border-radius:11px;background:var(--surface-soft)}.range-grid label>div{display:flex;justify-content:space-between;margin-bottom:10px;color:var(--text-muted);font-size:10px}.range-grid strong{color:var(--gold-300)}.range-grid input{width:100%;accent-color:var(--cyan-400)}.work-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.work-grid label{padding:10px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft)}.work-grid label>span{display:block;margin-bottom:7px;color:var(--text-muted);font-size:9px}.work-grid .field-select{height:34px}.skill-list{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.skill-list article,.equipped-slots article{min-height:58px;padding:10px 11px;display:flex;align-items:center;justify-content:space-between;gap:10px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft)}.skill-list strong,.skill-list small,.equipped-slots strong,.equipped-slots small{display:block}.skill-list strong,.equipped-slots strong{color:var(--text-strong);font-size:10px}.skill-list small,.equipped-slots small{max-width:230px;margin-top:4px;overflow:hidden;color:var(--text-faint);font-size:7px;white-space:nowrap;text-overflow:ellipsis}.skill-list button,.equipped-slots button{border:0;border-radius:7px;background:rgba(255,255,255,.04);color:var(--text-muted);font-size:8px;cursor:pointer}.skill-list button:hover,.equipped-slots button:hover{color:var(--cyan-300)}.skill-list.compact{grid-template-columns:1fr;max-height:310px;overflow:auto}.skill-list.compact article>div:last-child{display:flex;gap:4px}.skill-add{margin-top:11px;display:grid;grid-template-columns:1fr auto;gap:8px}.dual-skills{display:grid;grid-template-columns:1.25fr .75fr;gap:16px}.dual-skills h4{margin:0 0 9px;color:var(--text-muted);font-size:10px}.equipped-slots{display:grid;gap:8px}.equipped-slots article{min-height:64px}.equipped-slots .empty-slot{justify-content:center;color:var(--text-faint);border-style:dashed}.flag-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:9px}.flag-grid label{height:44px;padding:0 13px;display:flex;align-items:center;gap:10px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft);color:var(--text);font-size:10px}.flag-grid input{accent-color:var(--cyan-400)}.retrieve{display:flex;align-items:center;justify-content:space-between}.raw-json{width:100%;height:260px;padding:13px;border:1px solid var(--border-subtle);border-radius:10px;resize:vertical;outline:0;background:#030b12;color:#9ec1ca;font:9px/1.55 Consolas,monospace}.danger-zone{margin-top:22px;padding:15px;display:flex;align-items:center;justify-content:space-between;gap:20px;border:1px solid rgba(217,78,92,.2);border-radius:11px;background:rgba(217,78,92,.05)}.danger-zone h3{margin:0;color:var(--red-300);font-size:12px}.danger-zone p{margin:5px 0 0;color:var(--text-muted);font-size:9px}.error-copy{margin:16px 0 0;color:var(--red-300);font-size:10px}.summary-card{position:sticky;top:98px;padding:17px}.summary-portrait{height:150px;display:grid;place-items:center;border:1px solid var(--border-subtle);border-radius:13px;background:radial-gradient(circle,rgba(35,197,216,.11),rgba(5,16,27,.4))}.summary-portrait img{width:140px;height:140px;object-fit:contain}.summary-card h3{margin:14px 0 4px;color:var(--text-strong);font-size:15px}.summary-card>p{margin:0;overflow:hidden;color:var(--text-faint);font-size:7px;white-space:nowrap;text-overflow:ellipsis}.summary-card dl{margin:16px 0 0}.summary-card dl div{min-height:42px;display:flex;align-items:center;justify-content:space-between;gap:12px;border-top:1px solid var(--border-subtle)}.summary-card dt{color:var(--text-muted);font-size:9px}.summary-card dd{margin:0;max-width:130px;overflow:hidden;color:var(--text);font-size:9px;text-align:right;white-space:nowrap;text-overflow:ellipsis}.summary-card dd.valid{display:flex;align-items:center;gap:5px;color:var(--green-300)}.dialog-copy{margin:0;color:var(--text-muted);font-size:12px;line-height:1.7}@keyframes spin{to{transform:rotate(360deg)}}
.raw-actions{display:flex;gap:8px}
@media(max-width:1366px){.editor-grid{grid-template-columns:minmax(0,1fr) 232px}.tabs button{padding:0 10px}.tab-content{padding:16px}.form-grid.three{grid-template-columns:repeat(2,1fr)}.work-grid{grid-template-columns:repeat(2,1fr)}}
</style>
