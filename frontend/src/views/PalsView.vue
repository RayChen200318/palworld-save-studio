<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import AppShell from '@/components/AppShell.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import StatusPill from '@/components/StatusPill.vue'
import VirtualPalGrid from '@/components/VirtualPalGrid.vue'
import { messages } from '@/i18n/messages'
import { useCatalogStore } from '@/stores/catalog'
import { useCollectionStore } from '@/stores/collection'
import { useDraftStore } from '@/stores/draft'
import { useSessionStore } from '@/stores/session'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const catalog = useCatalogStore()
const collection = useCollectionStore()
const draft = useDraftStore()
const copy = computed(() => messages[session.locale])
const addOpen = ref(false)
const owner = ref('')
const species = ref('')
const notice = ref('')
const owners = computed(() => collection.players)
const speciesOptions = computed(() => catalog.pals)
const elements = computed(() => [...new Set(collection.pals.flatMap((pal) => pal.Elements))].sort())

onMounted(async () => {
  await session.bootstrap()
  if (!session.loaded) {
    router.replace('/')
    return
  }
  await Promise.all([catalog.load(), collection.loadPals(), collection.loadPlayers()])
  if (route.query.anomaly === 'yes') collection.filters.anomaly = 'yes'
  if (route.query.add === '1') openAdd()
})

function openAdd() {
  owner.value = owner.value || owners.value[0]?.PlayerUId || ''
  species.value = species.value || speciesOptions.value.find((item) => !item.IsHuman)?.InternalName || ''
  addOpen.value = true
}

async function create() {
  if (!owner.value || !species.value) return
  const pal = await collection.createPal(owner.value, species.value)
  addOpen.value = false
  router.push(`/pals/${pal.InstanceId}`)
}

async function healAll() {
  await collection.healAll()
  notice.value = copy.value.pals.healed
  window.setTimeout(() => { notice.value = '' }, 2800)
}
</script>

<template>
  <AppShell :eyebrow="copy.pals.eyebrow" :title="copy.pals.title">
    <section class="collection-heading"><div><p>{{ copy.pals.intro }}</p><StatusPill tone="cyan">{{ collection.filteredPals.length }} {{ copy.pals.total }}</StatusPill></div><div><button class="button secondary" type="button" :disabled="draft.pending" @click="healAll"><AppIcon name="heart" :size="16" />{{ copy.pals.heal }}</button><button class="button primary" type="button" @click="openAdd"><AppIcon name="plus" :size="16" />{{ copy.pals.add }}</button></div></section>

    <section class="filter-panel panel">
      <label><span>{{ copy.pals.ownerFilter }}</span><select v-model="collection.filters.owner" class="field-select"><option value="">{{ copy.common.all }}</option><option v-for="player in owners" :key="player.PlayerUId" :value="player.PlayerUId">{{ player.NickName }}</option></select></label>
      <label><span>{{ copy.pals.locationFilter }}</span><select v-model="collection.filters.location" class="field-select"><option value="">{{ copy.common.all }}</option><option v-for="(label, key) in copy.locations" :key="key" :value="key">{{ label }}</option></select></label>
      <label><span>{{ copy.pals.elementFilter }}</span><select v-model="collection.filters.element" class="field-select"><option value="">{{ copy.common.all }}</option><option v-for="element in elements" :key="element" :value="element">{{ element }}</option></select></label>
      <label><span>{{ copy.pals.typeFilter }}</span><select v-model="collection.filters.objectType" class="field-select"><option value="">{{ copy.common.all }}</option><option value="pal">{{ copy.pals.typePal }}</option><option value="human">{{ copy.pals.typeHuman }}</option></select></label>
      <label><span>{{ copy.pals.anomalyFilter }}</span><select v-model="collection.filters.anomaly" class="field-select"><option value="">{{ copy.common.all }}</option><option value="no">{{ copy.pals.normal }}</option><option value="yes">{{ copy.pals.anomalous }}</option></select></label>
      <label><span>{{ copy.pals.sort }}</span><select v-model="collection.filters.sort" class="field-select"><option value="deck">{{ copy.pals.sortDeck }}</option><option value="level">{{ copy.pals.sortLevel }}</option><option value="name">{{ copy.pals.sortName }}</option><option value="owner">{{ copy.pals.sortOwner }}</option></select></label>
    </section>

    <div v-if="collection.loading" class="loading"><AppIcon name="refresh" />{{ copy.common.loading }}</div>
    <VirtualPalGrid v-else :items="collection.filteredPals" :overscan="4" />
    <div v-if="notice" class="toast"><AppIcon name="check" :size="16" />{{ notice }}</div>

    <ModalDialog :open="addOpen" :title="copy.pals.addTitle" width="620px" @close="addOpen = false">
      <div class="add-form"><label><span class="field-label">{{ copy.pals.chooseOwner }}</span><select v-model="owner" class="field-select"><option v-for="player in owners" :key="player.PlayerUId" :value="player.PlayerUId">{{ player.NickName }} · {{ player.PlayerUId }}</option></select></label><label><span class="field-label">{{ copy.pals.chooseSpecies }}</span><select v-model="species" class="field-select"><option v-for="item in speciesOptions" :key="item.InternalName" :value="item.InternalName">{{ item.I18n }} · {{ item.InternalName }}</option></select></label><div class="destination"><AppIcon name="box" :size="19" /><span>{{ copy.pals.destination }}</span></div><p v-if="draft.error" class="error">{{ draft.error }}</p></div>
      <template #footer><button class="button secondary" type="button" @click="addOpen = false">{{ copy.common.cancel }}</button><button class="button primary" type="button" :disabled="!owner || !species || draft.pending" @click="create">{{ copy.pals.create }}</button></template>
    </ModalDialog>
  </AppShell>
</template>

<style scoped>
.collection-heading{margin-bottom:12px;display:flex;align-items:center;justify-content:space-between;gap:20px}.collection-heading>div:first-child{display:flex;align-items:center;gap:12px}.collection-heading p{max-width:820px;margin:0;color:var(--text-muted);font-size:14px;line-height:1.5}.collection-heading>div:last-child{display:flex;gap:9px}.filter-panel{margin-bottom:10px;padding:11px;display:grid;grid-template-columns:repeat(6,minmax(120px,1fr));gap:9px}.filter-panel label>span{display:block;margin:0 0 5px;color:var(--text-faint);font-size:12px;font-weight:700}.filter-panel .field-select{height:40px;font-size:13px}.loading{height:420px;display:grid;place-items:center;align-content:center;gap:10px;color:var(--text-muted);font-size:13px}.loading .app-icon{animation:spin 1s linear infinite}.toast{position:fixed;right:28px;bottom:26px;z-index:50;padding:12px 15px;display:flex;align-items:center;gap:9px;border:1px solid rgba(85,214,165,.28);border-radius:11px;background:rgba(13,35,33,.96);color:var(--green-300);font-size:13px;box-shadow:var(--shadow-float)}.add-form{display:grid;gap:17px}.destination{padding:13px;display:flex;align-items:center;gap:10px;border:1px solid rgba(53,230,209,.18);border-radius:11px;background:rgba(53,230,209,.07);color:var(--cyan-300);font-size:13px}.error{margin:0;color:var(--red-300);font-size:13px}@keyframes spin{to{transform:rotate(360deg)}}
@media(max-width:1366px){.filter-panel{grid-template-columns:repeat(3,1fr)}}
</style>
