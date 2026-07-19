<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import AppShell from '@/components/AppShell.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import SearchCatalogBrowser from '@/components/SearchCatalogBrowser.vue'
import SearchableSelect from '@/components/SearchableSelect.vue'
import StatusPill from '@/components/StatusPill.vue'
import { messages } from '@/i18n/messages'
import { apiClient } from '@/services/apiClient'
import { useCatalogStore } from '@/stores/catalog'
import { useCollectionStore } from '@/stores/collection'
import { useDraftStore } from '@/stores/draft'
import { useSessionStore } from '@/stores/session'
import type { ActiveSkill, PalDetail, PassiveSkill, SearchBrowserOption, SearchSelectOption } from '@/types/domain'

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
const passiveFilter = ref<'all' | 'mutation'>('all')
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
const species = computed(() => form.value
  ? catalog.palById.get(form.value.SpeciesKey) || catalog.palById.get(form.value.CharacterID)
  : undefined)
const currentSpeciesName = computed(() => species.value?.I18n[session.locale] || species.value?.I18n.en || form.value?.SpeciesName || '')
const speciesPickerOptions = computed<SearchSelectOption[]>(() => catalog.pals.map((item) => ({
  value: item.InternalName,
  title: item.I18n[session.locale] || item.I18n.en || item.InternalName,
  subtitle: item.InternalName,
  meta: item.SortingKey ? `${copy.value.pals.paldeck} #${item.SortingKey}` : '',
  badge: item.IsHuman ? copy.value.pals.typeHuman : copy.value.pals.typePal,
  iconUrl: `/image/pals/${item.IconAccessKey}`,
  searchText: `${item.I18n.en} ${item.I18n['zh-CN']} ${item.InternalName} ${item.SortingKey || ''}`,
})))
const availablePassives = computed(() => catalog.passives.filter((item) =>
  !form.value?.PassiveSkillList.includes(item.InternalName)
  && (passiveFilter.value === 'all' || item.IsMutationExclusive),
))
const availableActives = computed(() => catalog.actives.filter((item) => !form.value?.MasteredWaza.includes(item.InternalName)))
const passivePickerOptions = computed<SearchBrowserOption[]>(() => availablePassives.value.map((skill) => ({
  value: skill.InternalName,
  title: passiveName(skill.InternalName),
  subtitle: skill.InternalName,
  summary: passiveDescription(skill.InternalName),
  badge: skill.IsMutationExclusive ? copy.value.pal.mutationExclusive : '',
  meta: `${copy.value.pal.rating} ${skill.Rating}`,
  searchText: `${skill.I18n.en.Name} ${skill.I18n.en.Description} ${skill.I18n['zh-CN'].Name} ${skill.I18n['zh-CN'].Description} ${skill.InternalName}`,
})))
const activePickerOptions = computed<SearchBrowserOption[]>(() => availableActives.value.map((skill) => ({
  value: skill.InternalName,
  title: activeName(skill.InternalName),
  subtitle: skill.InternalName,
  summary: activeDescription(skill.InternalName),
  meta: `${copy.value.pal.power} ${skill.Power} · ${copy.value.pal.cooldown} ${skill.CT}${copy.value.pal.seconds}`,
  searchText: `${skill.I18n.en.Name} ${skill.I18n.en.Description} ${skill.I18n['zh-CN'].Name} ${skill.I18n['zh-CN'].Description} ${skill.InternalName} ${skill.Element}`,
})))
const workKeys = computed(() => {
  const currentSpecies = species.value
  if (!form.value || !currentSpecies) return []
  return Object.keys(currentSpecies.Suitabilities).filter((key) => currentSpecies.Suitabilities[key] > 0)
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

function changeSpecies(value: string) {
  if (value && value !== form.value?.CharacterID) apply({ CharacterID: value })
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
function workMinimum(key: string) {
  const base = species.value?.Suitabilities[key] || 0
  return Math.min(10, base + ((form.value?.Rank || 1) >= 5 ? 1 : 0))
}
function workRanks(key: string) {
  const minimum = workMinimum(key)
  return Array.from({ length: 11 - minimum }, (_, index) => minimum + index)
}
function passiveSkill(key: string): PassiveSkill | undefined { return catalog.passiveById.get(key) }
function activeSkill(key: string): ActiveSkill | undefined { return catalog.activeById.get(key) }
function passiveName(key: string) { return passiveSkill(key)?.I18n[session.locale].Name || key }
function passiveDescription(key: string) { return passiveSkill(key)?.I18n[session.locale].Description || copy.value.pal.descriptionUnavailable }
function activeName(key: string) { return activeSkill(key)?.I18n[session.locale].Name || key }
function activeDescription(key: string) { return activeSkill(key)?.I18n[session.locale].Description || copy.value.pal.descriptionUnavailable }
function activeMetrics(key: string) {
  const skill = activeSkill(key)
  return skill ? `${skill.Element} · ${copy.value.pal.power} ${skill.Power} · ${copy.value.pal.cooldown} ${skill.CT}${copy.value.pal.seconds}` : key
}

onMounted(load)
watch(instanceId, load)
</script>

<template>
  <AppShell :eyebrow="copy.pal.eyebrow" :title="currentSpeciesName || copy.common.loading">
    <div v-if="!form" class="loading"><AppIcon name="refresh" />{{ copy.common.loading }}</div>
    <template v-else>
      <RouterLink to="/pals" class="back-link"><AppIcon name="arrow-left" :size="15" />{{ copy.pal.back }}</RouterLink>
      <section class="pal-hero panel">
        <div class="pal-portrait"><img :src="`/image/pals/${form.IconAccessKey}`" alt="" /></div>
        <div class="pal-title"><div><StatusPill :tone="form.ObjectType === 'human' ? 'gold' : 'cyan'">{{ form.ObjectType === 'human' ? copy.pals.typeHuman : copy.pals.typePal }}</StatusPill><StatusPill v-if="form.IsAnomalous" tone="red">{{ copy.pals.anomalous }}</StatusPill></div><h2>{{ currentSpeciesName }}</h2><p>{{ form.NickName || form.CharacterID }} · {{ copy.pal.ownedBy }} {{ form.OwnerName || copy.common.none }}</p></div>
        <div class="hero-actions"><button class="button secondary" type="button" :disabled="draft.pending" @click="duplicate"><AppIcon name="copy" :size="16" />{{ copy.pal.duplicate }}</button><button class="button danger" type="button" @click="deleteOpen = true"><AppIcon name="trash" :size="16" />{{ copy.pal.remove }}</button></div>
      </section>

      <section class="editor-grid">
        <article class="panel editor-panel">
          <nav class="tabs"><button v-for="[key, label] in tabs" :key="key" type="button" :class="{ active: activeTab === key }" @click="activeTab = key">{{ label }}</button></nav>
          <div class="tab-content">
            <template v-if="activeTab === 'base'">
              <section class="editor-section"><div class="section-heading"><h3>{{ copy.pal.identity }}</h3></div><div class="form-grid three"><label><span class="field-label">{{ copy.pal.species }}</span><SearchableSelect :model-value="form.CharacterID" :options="speciesPickerOptions" :placeholder="copy.pals.chooseSpecies" :search-placeholder="copy.pals.searchSpecies" :empty-text="copy.common.noResults" @update:model-value="changeSpecies" /></label><label><span class="field-label">{{ copy.pal.nickname }}</span><input class="field-input" :value="form.NickName" maxlength="64" @blur="stringChange('NickName', $event)" /></label><label><span class="field-label">{{ copy.pal.gender }}</span><select class="field-select" :value="form.Gender || ''" :disabled="form.IsHuman" @change="selectChange('Gender', $event)"><option value="EPalGenderType::Male">{{ copy.pal.male }}</option><option value="EPalGenderType::Female">{{ copy.pal.female }}</option></select></label></div></section>
              <section class="editor-section"><div class="section-heading"><h3>{{ copy.pal.progression }}</h3></div><div class="form-grid three"><label><span class="field-label">{{ copy.common.level }}</span><input class="field-input" type="number" min="1" max="80" :value="form.Level" @blur="numberChange('Level', $event)" /></label><label><span class="field-label">{{ copy.pal.friendship }}</span><input class="field-input" type="number" min="-3" max="10" :value="form.FriendshipLevel" @blur="numberChange('FriendshipLevel', $event)" /></label><label><span class="field-label">{{ copy.pal.condensation }}</span><select class="field-select" :value="form.Rank" @change="numberChange('Rank', $event)"><option v-for="rank in 5" :key="rank" :value="rank">{{ rank - 1 }} ★</option></select></label></div></section>
              <section class="editor-section"><div class="section-heading"><h3>{{ copy.pal.computed }}</h3></div><div class="stat-cards"><div><span>{{ copy.pal.hp }}</span><strong>{{ form.ComputedMaxHP ?? '—' }}</strong></div><div><span>{{ copy.pal.attack }}</span><strong>{{ form.ComputedAttack ?? '—' }}</strong></div><div><span>{{ copy.pal.defense }}</span><strong>{{ form.ComputedDefense ?? '—' }}</strong></div><div><span>{{ copy.pal.workSpeed }}</span><strong>{{ form.ComputedCraftSpeed ?? '—' }}</strong></div></div></section>
            </template>

            <template v-else-if="activeTab === 'stats'">
              <section class="editor-section"><div class="section-heading"><h3>{{ copy.pal.iv }}</h3></div><div class="range-grid"><label v-for="field in statFields" :key="field.key"><div><span>{{ field.label }}</span><strong>{{ form[field.key] }}</strong></div><input type="range" min="0" max="100" :value="form[field.key]" @change="numberChange(field.key, $event)" /></label></div></section>
              <section class="editor-section"><div class="section-heading"><h3>{{ copy.pal.soul }}</h3></div><div class="range-grid"><label v-for="field in soulFields" :key="field.key"><div><span>{{ field.label }}</span><strong>{{ form[field.key] }} / 20</strong></div><input type="range" min="0" max="20" :value="form[field.key]" @change="numberChange(field.key, $event)" /></label></div></section>
            </template>

            <template v-else-if="activeTab === 'work'">
              <section class="editor-section"><div class="section-heading"><div><h3>{{ copy.pal.workTitle }}</h3><p>{{ copy.pal.workHint }}</p></div></div><div class="work-grid"><label v-for="key in workKeys" :key="key"><span>{{ workLabel(key) }}</span><select class="field-select" :value="form.Suitabilities[key] || workMinimum(key)" @change="apply({ Suitabilities: { [key]: Number(($event.target as HTMLSelectElement).value) } })"><option v-for="rank in workRanks(key)" :key="rank" :value="rank">Lv. {{ rank }}</option></select></label></div></section>
            </template>

            <template v-else-if="activeTab === 'passives'">
              <section class="editor-section"><div class="section-heading"><div><h3>{{ copy.pal.passivesTitle }}</h3><p>{{ copy.pal.passivesHint }}</p></div><StatusPill :tone="form.PassiveSkillList.length >= 4 ? 'gold' : 'cyan'">{{ form.PassiveSkillList.length }} / 4</StatusPill></div><div class="skill-list detailed"><article v-for="skill in form.PassiveSkillList" :key="skill"><div><div class="skill-title"><strong>{{ passiveName(skill) }}</strong><StatusPill v-if="passiveSkill(skill)?.IsMutationExclusive" tone="gold">{{ copy.pal.mutationExclusive }}</StatusPill></div><p>{{ passiveDescription(skill) }}</p><small>{{ skill }} · {{ copy.pal.rating }} {{ passiveSkill(skill)?.Rating ?? '—' }}</small></div><button type="button" @click="removePassive(skill)"><AppIcon name="trash" :size="15" /></button></article></div><div class="skill-filter"><button type="button" :class="{ active: passiveFilter === 'all' }" @click="passiveFilter = 'all'">{{ copy.pal.allPassives }}</button><button type="button" :class="{ active: passiveFilter === 'mutation' }" @click="passiveFilter = 'mutation'">{{ copy.pal.mutationPassives }}</button></div><SearchCatalogBrowser v-model="passiveToAdd" :options="passivePickerOptions" :search-placeholder="copy.pal.searchPassive" :empty-text="copy.common.noResults"><template #preview="{ option }"><template v-if="option"><span class="preview-label">{{ copy.pal.selectedSkill }}</span><h4>{{ option.title }}</h4><code>{{ option.subtitle }}</code><div class="preview-tags"><StatusPill tone="gold">{{ copy.pal.rating }} {{ passiveSkill(option.value)?.Rating }}</StatusPill><StatusPill v-if="passiveSkill(option.value)?.IsMutationExclusive" tone="gold">{{ copy.pal.mutationExclusive }}</StatusPill></div><p>{{ passiveDescription(option.value) }}</p></template><p v-else>{{ copy.common.noResults }}</p></template></SearchCatalogBrowser><div class="skill-add-action"><button class="button secondary" type="button" :disabled="!passiveToAdd || form.PassiveSkillList.length >= 4" @click="addPassive"><AppIcon name="plus" :size="15" />{{ copy.pal.addPassive }}</button></div></section>
            </template>

            <template v-else-if="activeTab === 'actives'">
              <section class="editor-section"><div class="section-heading"><div><h3>{{ copy.pal.activeHint }}</h3></div></div><div class="dual-skills"><div><h4>{{ copy.pal.mastered }}</h4><div class="skill-list compact detailed"><article v-for="skill in form.MasteredWaza" :key="skill"><div><strong>{{ activeName(skill) }}</strong><p>{{ activeDescription(skill) }}</p><small>{{ activeMetrics(skill) }}</small></div><div><button v-if="!form.EquipWaza.includes(skill)" type="button" :disabled="form.EquipWaza.length >= 3" @click="equip(skill)">{{ copy.pal.equip }}</button><button type="button" @click="forget(skill)">{{ copy.pal.forget }}</button></div></article></div></div><div><h4>{{ copy.pal.equipped }} · {{ form.EquipWaza.length }} / 3</h4><div class="equipped-slots"><article v-for="skill in form.EquipWaza" :key="skill"><span><strong>{{ activeName(skill) }}</strong><small>{{ activeMetrics(skill) }}</small></span><button type="button" @click="unequip(skill)">{{ copy.pal.unequip }}</button></article><article v-for="slot in (3 - form.EquipWaza.length)" :key="`empty-${slot}`" class="empty-slot">—</article></div></div></div><div class="active-browser"><SearchCatalogBrowser v-model="activeToAdd" :options="activePickerOptions" :search-placeholder="copy.pal.searchActive" :empty-text="copy.common.noResults"><template #preview="{ option }"><template v-if="option"><span class="preview-label">{{ copy.pal.selectedSkill }}</span><h4>{{ option.title }}</h4><code>{{ option.subtitle }}</code><div class="skill-metrics"><span>{{ copy.pal.element }}<strong>{{ activeSkill(option.value)?.Element }}</strong></span><span>{{ copy.pal.power }}<strong>{{ activeSkill(option.value)?.Power }}</strong></span><span>{{ copy.pal.cooldown }}<strong>{{ activeSkill(option.value)?.CT }}{{ copy.pal.seconds }}</strong></span></div><p :class="{ unavailable: !activeSkill(option.value)?.I18n[session.locale].Description }">{{ activeDescription(option.value) }}</p></template><p v-else>{{ copy.common.noResults }}</p></template></SearchCatalogBrowser><div class="skill-add-action"><button class="button secondary" type="button" :disabled="!activeToAdd" @click="addMastered"><AppIcon name="plus" :size="15" />{{ copy.pal.addActive }}</button></div></div></section>
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

        <aside class="panel summary-card"><div class="summary-portrait"><img :src="`/image/pals/${form.IconAccessKey}`" alt="" /></div><h3>{{ currentSpeciesName }}</h3><p>{{ form.InstanceId }}</p><dl><div><dt>{{ copy.pal.objectType }}</dt><dd>{{ form.ObjectType === 'human' ? copy.pals.typeHuman : copy.pals.typePal }}</dd></div><div><dt>{{ copy.common.location }}</dt><dd>{{ copy.locations[form.Location] }}</dd></div><div><dt>{{ copy.common.owner }}</dt><dd>{{ form.OwnerName || copy.common.none }}</dd></div><div><dt>{{ copy.pal.passivesCount }}</dt><dd>{{ form.PassiveSkillList.length }} / 4</dd></div><div><dt>{{ copy.pal.activesCount }}</dt><dd>{{ form.EquipWaza.length }} / 3</dd></div><div><dt>{{ copy.pal.integrity }}</dt><dd class="valid"><AppIcon name="check" :size="13" />{{ copy.pal.valid }}</dd></div></dl></aside>
      </section>
    </template>

    <ModalDialog :open="deleteOpen" :title="copy.pal.deleteTitle" @close="deleteOpen = false"><p class="dialog-copy">{{ copy.pal.deleteCopy }}</p><template #footer><button class="button secondary" type="button" @click="deleteOpen = false">{{ copy.common.cancel }}</button><button class="button danger" type="button" :disabled="draft.pending" @click="remove">{{ copy.pal.remove }}</button></template></ModalDialog>
  </AppShell>
</template>

<style scoped>
.loading{height:500px;display:grid;place-items:center;align-content:center;gap:12px;color:var(--text-muted);font-size:13px}.loading .app-icon{animation:spin 1s linear infinite}.back-link{display:inline-flex;align-items:center;gap:7px;margin-bottom:10px;color:var(--text-muted);font-size:13px;text-decoration:none}.back-link:hover{color:var(--cyan-300)}.pal-hero{padding:13px 16px;display:flex;align-items:center;gap:15px}.pal-portrait{width:76px;height:76px;display:grid;place-items:center;border:1px solid var(--border-violet);border-radius:13px;background:radial-gradient(circle,rgba(53,230,209,.12),rgba(139,124,255,.07),rgba(5,9,17,.5))}.pal-portrait img{width:72px;height:72px;object-fit:contain}.pal-title{min-width:0;flex:1}.pal-title>div{display:flex;gap:6px}.pal-title :deep(.status-pill){font-size:12px}.pal-title h2{margin:6px 0 2px;color:var(--text-strong);font-size:22px}.pal-title p{margin:0;color:var(--text-muted);font-size:13px}.hero-actions{display:flex;gap:8px}.editor-grid{margin-top:12px;display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:12px;align-items:start}.tabs{height:48px;padding:0 8px;display:flex;align-items:end;border-bottom:1px solid var(--border-subtle);overflow:auto}.tabs button{height:47px;padding:0 14px;border:0;border-bottom:2px solid transparent;background:transparent;color:var(--text-muted);font:inherit;font-size:13px;font-weight:700;white-space:nowrap;cursor:pointer}.tabs button:hover{color:var(--text-strong)}.tabs button.active{border-color:var(--violet-300);color:var(--cyan-200);background:linear-gradient(0deg,rgba(139,124,255,.1),transparent)}.tab-content{padding:18px}.editor-section+.editor-section{margin-top:18px;padding-top:17px;border-top:1px solid var(--border-subtle)}.section-heading{margin-bottom:12px;display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.section-heading h3,.retrieve h3{margin:0;color:var(--text-strong);font-size:16px}.section-heading p,.retrieve p{margin:4px 0 0;color:var(--text-muted);font-size:13px;line-height:1.5}.form-grid{display:grid;gap:11px}.form-grid.three{grid-template-columns:repeat(3,1fr)}.stat-cards{display:grid;grid-template-columns:repeat(4,1fr);gap:9px}.stat-cards div{padding:12px 13px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft)}.stat-cards span{display:block;color:var(--text-faint);font-size:12px}.stat-cards strong{display:block;margin-top:5px;color:var(--cyan-200);font-size:20px}.range-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:11px}.range-grid label{padding:13px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft)}.range-grid label>div{display:flex;justify-content:space-between;margin-bottom:10px;color:var(--text-muted);font-size:13px}.range-grid strong{color:var(--violet-200)}.range-grid input{width:100%;accent-color:var(--cyan-300)}.work-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.work-grid label{padding:10px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft)}.work-grid label>span{display:block;margin-bottom:6px;color:var(--text-muted);font-size:13px}.work-grid .field-select{height:40px}.skill-list{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.skill-list article,.equipped-slots article{min-height:62px;padding:10px 11px;display:flex;align-items:center;justify-content:space-between;gap:10px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft)}.skill-list strong,.skill-list small,.equipped-slots strong,.equipped-slots small{display:block}.skill-list strong,.equipped-slots strong{color:var(--text-strong);font-size:13px}.skill-list small,.equipped-slots small{max-width:230px;margin-top:3px;overflow:hidden;color:var(--text-faint);font-size:11px;white-space:nowrap;text-overflow:ellipsis}.skill-list button,.equipped-slots button{min-height:30px;padding:0 8px;border:0;border-radius:7px;background:rgba(255,255,255,.05);color:var(--text-muted);font-size:12px;cursor:pointer}.skill-list button:hover,.equipped-slots button:hover{color:var(--cyan-300);background:var(--surface-hover)}.skill-list.compact{grid-template-columns:1fr;max-height:330px;overflow:auto}.skill-list.compact article>div:last-child{display:flex;gap:4px}.skill-add{margin-top:11px;display:grid;grid-template-columns:1fr auto;gap:8px}.dual-skills{display:grid;grid-template-columns:1.25fr .75fr;gap:16px}.dual-skills h4{margin:0 0 9px;color:var(--text-muted);font-size:14px}.equipped-slots{display:grid;gap:8px}.equipped-slots article{min-height:64px}.equipped-slots .empty-slot{justify-content:center;color:var(--text-faint);border-style:dashed}.flag-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:9px}.flag-grid label{height:46px;padding:0 13px;display:flex;align-items:center;gap:10px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft);color:var(--text);font-size:14px}.flag-grid input{accent-color:var(--cyan-300)}.retrieve{display:flex;align-items:center;justify-content:space-between}.raw-json{width:100%;height:260px;padding:13px;border:1px solid var(--border-subtle);border-radius:10px;resize:vertical;outline:0;background:#05070d;color:#a9c8ce;font:12px/1.55 Consolas,monospace}.danger-zone{margin-top:18px;padding:14px;display:flex;align-items:center;justify-content:space-between;gap:20px;border:1px solid rgba(255,122,138,.22);border-radius:11px;background:rgba(232,91,112,.06)}.danger-zone h3{margin:0;color:var(--red-300);font-size:15px}.danger-zone p{margin:4px 0 0;color:var(--text-muted);font-size:13px}.error-copy{margin:15px 0 0;color:var(--red-300);font-size:13px}.summary-card{position:sticky;top:88px;padding:16px}.summary-portrait{height:136px;display:grid;place-items:center;border:1px solid var(--border-violet);border-radius:12px;background:radial-gradient(circle,rgba(53,230,209,.1),rgba(139,124,255,.07),rgba(5,9,17,.45))}.summary-portrait img{width:130px;height:130px;object-fit:contain}.summary-card h3{margin:13px 0 3px;color:var(--text-strong);font-size:18px}.summary-card>p{margin:0;overflow:hidden;color:var(--text-faint);font-size:11px;white-space:nowrap;text-overflow:ellipsis}.summary-card dl{margin:14px 0 0}.summary-card dl div{min-height:42px;display:flex;align-items:center;justify-content:space-between;gap:12px;border-top:1px solid var(--border-subtle)}.summary-card dt{color:var(--text-muted);font-size:12px}.summary-card dd{margin:0;max-width:160px;overflow:hidden;color:var(--text);font-size:12px;text-align:right;white-space:nowrap;text-overflow:ellipsis}.summary-card dd.valid{display:flex;align-items:center;gap:5px;color:var(--green-300)}.dialog-copy{margin:0;color:var(--text-muted);font-size:14px;line-height:1.7}@keyframes spin{to{transform:rotate(360deg)}}
.raw-actions{display:flex;gap:8px}
.skill-list.detailed article{align-items:flex-start}.skill-list.detailed article>div:first-child{min-width:0;flex:1}.skill-list.detailed p{margin:6px 0 5px;color:var(--text-muted);font-size:12px;line-height:1.5}.skill-list.detailed small{max-width:none}.skill-title{display:flex;align-items:center;gap:7px}.skill-title :deep(.status-pill){min-height:22px;padding:2px 7px;font-size:12px}.skill-filter{margin:13px 0 9px;display:flex;gap:7px}.skill-filter button{height:34px;padding:0 11px;border:1px solid var(--border-subtle);border-radius:8px;background:var(--surface-soft);color:var(--text-muted);font:inherit;font-size:12px;font-weight:700;cursor:pointer}.skill-filter button.active{border-color:var(--border-violet);background:var(--surface-selected);color:var(--cyan-200)}.skill-add-action{margin-top:9px;display:flex;justify-content:flex-end}.preview-label{display:block;margin-bottom:5px;color:var(--cyan-300);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}.preview-tags{margin-top:12px;display:flex;flex-wrap:wrap;gap:6px}.skill-metrics{margin-top:13px;display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.skill-metrics span{padding:8px;border:1px solid var(--border-subtle);border-radius:8px;color:var(--text-faint);font-size:12px}.skill-metrics strong{display:block;margin-top:3px;color:var(--text-strong);font-size:13px}.unavailable{color:var(--gold-300)!important}.active-browser{margin-top:14px;padding-top:14px;border-top:1px solid var(--border-subtle)}
@media(max-width:1366px){.editor-grid{grid-template-columns:minmax(0,1fr) 276px}.tabs button{padding:0 10px}.tab-content{padding:16px}.form-grid.three{grid-template-columns:repeat(2,1fr)}.work-grid{grid-template-columns:repeat(2,1fr)}}
</style>
