<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/AppIcon.vue'
import AppShell from '@/components/AppShell.vue'
import ModalDialog from '@/components/ModalDialog.vue'
import SearchableSelect from '@/components/SearchableSelect.vue'
import StatusPill from '@/components/StatusPill.vue'
import { messages } from '@/i18n/messages'
import { useCatalogStore } from '@/stores/catalog'
import { useCollectionStore } from '@/stores/collection'
import { useDraftStore } from '@/stores/draft'
import { useItemsStore } from '@/stores/items'
import { useSessionStore } from '@/stores/session'
import type { ItemCatalogEntry, ItemContainerName, ItemSlot, SearchSelectOption } from '@/types/domain'

const router = useRouter()
const session = useSessionStore()
const catalog = useCatalogStore()
const collection = useCollectionStore()
const draft = useDraftStore()
const items = useItemsStore()
const copy = computed(() => messages[session.locale])
const addOpen = ref(false)
const deleteOpen = ref(false)
const chosenStaticId = ref('')
const addQuantity = ref(1)
const eggCharacterId = ref('')
const moveContainer = ref<ItemContainerName>('common')
const moveSlot = ref<number | null>(null)
const dragged = ref<{ Container: ItemContainerName; SlotIndex: number } | null>(null)
const localError = ref('')

const inventory = computed(() => items.inventory)
const activeContainer = computed(() => items.activeContainer)
const selected = computed(() => items.selectedSlot)
const selectedItem = computed(() => selected.value?.Item || null)
const systemManaged = computed(() => selectedItem.value?.ManagedKind === 'system')
const invalidQuantity = computed(() => selectedItem.value?.StateFlags.includes('invalid-quantity') || false)
const selectedCatalog = computed(() => {
  const id = selectedItem.value?.StaticId
  return id && items.catalog ? items.catalog.Items[id] : null
})
const chosenEntry = computed(() => chosenStaticId.value && items.catalog
  ? items.catalog.Items[chosenStaticId.value]
  : null)
const visibleCatalog = computed(() => items.filteredCatalog.slice(0, 160))
const dangerousDelete = computed(() => selectedItem.value?.Category === 'key')
const combinedError = computed(() => localError.value || items.error || draft.error)
const moveSlots = computed(() => {
  if (!inventory.value || moveContainer.value === 'drop') return []
  return inventory.value.Containers[moveContainer.value].Slots.filter((slot) => slot.Unlocked)
})
const eggSpeciesOptions = computed<SearchSelectOption[]>(() => (items.catalog?.EggSpecies || []).map((pal) => {
  const species = catalog.palById.get(pal.CharacterId)
  const sortingKey = species?.SortingKey || ''
  return {
    value: pal.CharacterId,
    title: pal.I18n[session.locale] || pal.I18n.en || pal.CharacterId,
    subtitle: pal.CharacterId,
    meta: sortingKey ? `${copy.value.pals.paldeck} #${sortingKey}` : '',
    badge: copy.value.pals.typePal,
    iconUrl: `/image/pals/${pal.IconAccessKey}`,
    searchText: `${pal.I18n.en} ${pal.I18n['zh-CN']} ${pal.CharacterId} ${sortingKey}`,
  }
}))

function itemName(item: { I18n: { en: string; 'zh-CN': string }; StaticId: string }) {
  return item.I18n[session.locale] || item.I18n.en || item.StaticId
}

function rarityLabel(rarity: number | null) {
  if (rarity === null) return copy.value.items.unknown
  return copy.value.items.rarities[rarity as keyof typeof copy.value.items.rarities] || `${copy.value.items.rarity} ${rarity}`
}

function slotLabel(slot: ItemSlot) {
  if (slot.SlotType) {
    return copy.value.items.slotTypes[slot.SlotType as keyof typeof copy.value.items.slotTypes] || slot.SlotType
  }
  return `${copy.value.items.slot} ${slot.SlotIndex + 1}`
}

function stateLabel(flag: string) {
  if (flag === 'invalid-quantity') return copy.value.items.invalidQuantity
  if (flag === 'system-managed') return copy.value.items.systemManaged
  return flag
}

async function choosePlayer(playerId: string) {
  if (!playerId) return
  localError.value = ''
  await items.loadInventory(playerId, true)
}

function selectContainer(container: ItemContainerName) {
  items.selectContainer(container)
  moveContainer.value = container === 'drop' ? 'common' : container
  moveSlot.value = null
}

function firstEmpty(container: ItemContainerName): ItemSlot | null {
  const target = inventory.value?.Containers[container]
  return target?.Slots.find((slot) => slot.Unlocked && !slot.Item) || null
}

function openAdd(slot?: ItemSlot) {
  localError.value = ''
  if (items.selectedContainer === 'drop') return
  const target = slot && slot.Unlocked && !slot.Item ? slot : firstEmpty(items.selectedContainer)
  if (!target) {
    localError.value = copy.value.items.noEmptySlot
    return
  }
  items.selectSlot(target.SlotIndex)
  chosenStaticId.value = ''
  addQuantity.value = 1
  eggCharacterId.value = ''
  items.query = ''
  items.category = ''
  items.rarity = ''
  addOpen.value = true
}

function chooseCatalogItem(entry: ItemCatalogEntry) {
  chosenStaticId.value = entry.StaticId
  addQuantity.value = 1
  eggCharacterId.value = entry.DynamicType === 'egg' ? (items.catalog?.EggSpecies[0]?.CharacterId || '') : ''
}

async function createItem() {
  const entry = chosenEntry.value
  if (!entry || items.selectedSlotIndex === null) return
  localError.value = ''
  try {
    await items.addItem({
      StaticId: entry.StaticId,
      Container: items.selectedContainer,
      Quantity: entry.DynamicType ? 1 : addQuantity.value,
      SlotIndex: items.selectedSlotIndex,
      ...(entry.DynamicType === 'egg' ? { EggCharacterId: eggCharacterId.value } : {}),
    })
    addOpen.value = false
  } catch (error) {
    localError.value = error instanceof Error ? error.message : String(error)
  }
}

async function patchNumber(field: 'Quantity' | 'Durability' | 'Ammo', event: Event) {
  const value = Number((event.currentTarget as HTMLInputElement).value)
  if (!Number.isFinite(value)) return
  try {
    await items.patchSelected({ [field]: field === 'Durability' ? value : Math.trunc(value) })
  } catch (error) {
    localError.value = error instanceof Error ? error.message : String(error)
  }
}

async function repairQuantity() {
  try {
    await items.patchSelected({ Quantity: 1 })
  } catch (error) {
    localError.value = error instanceof Error ? error.message : String(error)
  }
}

async function patchVariant(event: Event) {
  try {
    await items.patchSelected({ StaticId: (event.currentTarget as HTMLSelectElement).value })
  } catch (error) {
    localError.value = error instanceof Error ? error.message : String(error)
  }
}

async function removeSelected() {
  try {
    await items.deleteSelected(dangerousDelete.value)
    deleteOpen.value = false
  } catch (error) {
    localError.value = error instanceof Error ? error.message : String(error)
  }
}

async function moveSelected() {
  if (!selected.value || moveSlot.value === null) return
  try {
    await items.move(
      { Container: selected.value.Container, SlotIndex: selected.value.SlotIndex },
      { Container: moveContainer.value, SlotIndex: moveSlot.value },
    )
    moveSlot.value = null
  } catch (error) {
    localError.value = error instanceof Error ? error.message : String(error)
  }
}

async function retrieveDropItem() {
  if (!selected.value) return
  const target = firstEmpty('common')
  if (!target) {
    localError.value = copy.value.items.noCommonSpace
    return
  }
  await items.move(
    { Container: 'drop', SlotIndex: selected.value.SlotIndex },
    { Container: 'common', SlotIndex: target.SlotIndex },
  )
}

function dragStart(slot: ItemSlot) {
  if (!slot.Item || slot.Item.ManagedKind === 'system') return
  dragged.value = { Container: slot.Container, SlotIndex: slot.SlotIndex }
}

async function dropOn(slot: ItemSlot) {
  if (!dragged.value || !slot.Unlocked || slot.Container === 'drop') return
  const source = dragged.value
  dragged.value = null
  if (source.Container === slot.Container && source.SlotIndex === slot.SlotIndex) return
  try {
    await items.move(source, { Container: slot.Container, SlotIndex: slot.SlotIndex })
  } catch (error) {
    localError.value = error instanceof Error ? error.message : String(error)
  }
}

watch(moveContainer, () => { moveSlot.value = null })

onMounted(async () => {
  await session.bootstrap()
  if (!session.loaded) {
    router.replace('/')
    return
  }
  try {
    await Promise.all([collection.loadPlayers(), items.loadCatalog(), catalog.load()])
    const playerId = items.selectedPlayerId || collection.players[0]?.PlayerUId
    if (playerId) await items.loadInventory(playerId)
  } catch (error) {
    localError.value = error instanceof Error ? error.message : String(error)
  }
})
</script>

<template>
  <AppShell :eyebrow="copy.items.eyebrow" :title="copy.items.title">
    <section class="items-toolbar panel">
      <div class="toolbar-field player-field">
        <label class="field-label">{{ copy.items.player }}</label>
        <select class="field-select" :value="items.selectedPlayerId" @change="choosePlayer(($event.currentTarget as HTMLSelectElement).value)">
          <option v-for="player in collection.players" :key="player.PlayerUId" :value="player.PlayerUId">{{ player.NickName }} · {{ player.PlayerUId.slice(0, 8) }}</option>
        </select>
      </div>
      <div class="toolbar-copy"><strong>{{ copy.items.intro }}</strong><span v-if="inventory">{{ inventory.PlayerName }} · {{ activeContainer?.Capacity || 0 }} {{ copy.items.unlockedSlots }}</span></div>
      <button class="button primary" type="button" :disabled="items.selectedContainer === 'drop' || items.loading" @click="openAdd()"><AppIcon name="plus" :size="16" />{{ copy.items.add }}</button>
    </section>

    <nav class="container-tabs" :aria-label="copy.items.containersLabel">
      <button v-for="container in items.containerNames" :key="container" type="button" :class="{ active: items.selectedContainer === container }" @click="selectContainer(container)">
        <AppIcon :name="container === 'weapon' ? 'bolt' : container === 'armor' ? 'shield' : container === 'drop' ? 'archive' : 'box'" :size="17" />
        <span>{{ copy.items.containers[container] }}</span>
        <small v-if="inventory">{{ inventory.Containers[container].Slots.filter((slot) => slot.Item).length }}/{{ inventory.Containers[container].Capacity }}</small>
      </button>
    </nav>

    <p v-if="combinedError" class="error-banner"><AppIcon name="alert" :size="16" />{{ combinedError }}</p>

    <section class="inventory-layout">
      <article class="panel inventory-panel">
        <div class="panel-header">
          <div><h2>{{ copy.items.containers[items.selectedContainer] }}</h2><p>{{ items.selectedContainer === 'drop' ? copy.items.dropHint : copy.items.dragHint }}</p></div>
          <StatusPill v-if="activeContainer" :tone="activeContainer.ReadOnlyTarget ? 'gold' : 'cyan'">{{ activeContainer.Capacity }} {{ copy.items.unlocked }}</StatusPill>
        </div>
        <div v-if="items.loading" class="inventory-empty">{{ copy.common.loading }}</div>
        <div v-else-if="activeContainer?.Slots.length" class="slot-grid" :class="`container-${items.selectedContainer}`">
          <button
            v-for="slot in activeContainer.Slots"
            :key="slot.SlotIndex"
            class="item-slot"
            :class="{ selected: items.selectedSlotIndex === slot.SlotIndex, locked: !slot.Unlocked, anomalous: slot.Item?.StateFlags.length }"
            type="button"
            :disabled="!slot.Unlocked && !slot.Item"
            :draggable="Boolean(slot.Item && slot.Item.ManagedKind !== 'system')"
            @click="items.selectSlot(slot.SlotIndex)"
            @dragstart="dragStart(slot)"
            @dragover.prevent
            @drop.prevent="dropOn(slot)"
          >
            <span class="slot-number">{{ slotLabel(slot) }}</span>
            <template v-if="slot.Item">
              <img v-if="slot.Item.IconKey" :src="`/image/items/${slot.Item.IconKey}`" alt="" loading="lazy" />
              <span v-else class="unknown-icon"><AppIcon name="alert" /></span>
              <strong>{{ itemName(slot.Item) }}</strong>
              <small class="slot-id">{{ slot.Item.StaticId }}</small>
              <b v-if="slot.Item.Quantity > 1">×{{ slot.Item.Quantity }}</b>
              <i v-if="slot.Item.StateFlags.length">!</i>
            </template>
            <template v-else>
              <span class="empty-mark"><AppIcon :name="slot.Unlocked ? 'plus' : 'shield'" :size="18" /></span>
              <small>{{ slot.Unlocked ? copy.items.empty : copy.items.locked }}</small>
            </template>
          </button>
        </div>
        <div v-else class="inventory-empty">{{ items.selectedContainer === 'drop' ? copy.items.noDrops : copy.common.noResults }}</div>
      </article>

      <aside class="panel detail-panel">
        <template v-if="selectedItem && selected">
          <header class="item-detail-head">
            <img v-if="selectedItem.IconKey" :src="`/image/items/${selectedItem.IconKey}`" alt="" loading="lazy" />
            <span v-else class="detail-unknown"><AppIcon name="alert" /></span>
            <div><span>{{ slotLabel(selected) }}</span><h2>{{ itemName(selectedItem) }}</h2><code>{{ selectedItem.StaticId }}</code></div>
          </header>
          <div class="tag-row">
            <StatusPill :tone="selectedItem.StateFlags.length ? 'red' : 'neutral'">{{ selectedItem.Category }}</StatusPill>
            <StatusPill :tone="selectedItem.Rarity && selectedItem.Rarity > 0 ? 'gold' : 'neutral'">{{ rarityLabel(selectedItem.Rarity) }}</StatusPill>
          </div>
          <div v-if="selectedItem.StateFlags.length" class="state-list"><span v-for="flag in selectedItem.StateFlags" :key="flag">{{ stateLabel(flag) }}</span></div>
          <div v-if="systemManaged" class="system-card"><AppIcon name="shield" :size="18" /><div><strong>{{ copy.items.systemManaged }}</strong><span>{{ copy.items.systemManagedHint }}</span></div></div>
          <div v-if="invalidQuantity && !systemManaged" class="repair-card"><div><strong>{{ copy.items.invalidQuantity }}</strong><span>{{ copy.items.invalidQuantityHint }}</span></div><button class="button secondary" type="button" :disabled="draft.pending" @click="repairQuantity">{{ copy.items.repairQuantity }}</button></div>

          <div v-if="!systemManaged" class="detail-fields">
            <label v-if="selectedItem.MaxStack !== 1"><span class="field-label">{{ copy.items.quantity }}</span><input class="field-input" type="number" min="1" :max="selectedItem.MaxStack || selectedItem.Quantity" :value="selectedItem.Quantity" @change="patchNumber('Quantity', $event)" /></label>
            <label v-if="selectedItem.Variants.length > 1"><span class="field-label">{{ copy.items.rarity }}</span><select class="field-select" :value="selectedItem.StaticId" @change="patchVariant"><option v-for="variant in selectedItem.Variants" :key="variant.StaticId" :value="variant.StaticId">{{ itemName(variant) }} · {{ rarityLabel(variant.Rarity) }}</option></select></label>
            <label v-if="selectedItem.Durability !== null"><span class="field-label">{{ copy.items.durability }}</span><input class="field-input" type="number" min="0" :max="selectedItem.MaxDurability || 0" step="0.1" :value="selectedItem.Durability" @change="patchNumber('Durability', $event)" /></label>
            <label v-if="selectedItem.Ammo !== null"><span class="field-label">{{ copy.items.ammo }}</span><input class="field-input" type="number" min="0" :max="selectedItem.MagazineSize || 0" :value="selectedItem.Ammo" @change="patchNumber('Ammo', $event)" /></label>
          </div>

          <div v-if="selectedItem.EggCharacterId" class="egg-card"><img :src="`/image/pals/${selectedItem.EggCharacterId}`" alt="" loading="lazy" /><div><span>{{ copy.items.eggSpecies }}</span><strong>{{ selectedItem.EggCharacterId }}</strong></div></div>
          <div v-if="selectedItem.PassiveSkills.length" class="passive-card"><span>{{ copy.items.readOnlyPassives }}</span><code v-for="skill in selectedItem.PassiveSkills" :key="skill">{{ skill }}</code></div>

          <div v-if="!systemManaged && items.selectedContainer === 'drop'" class="detail-actions"><button class="button primary" type="button" @click="retrieveDropItem"><AppIcon name="archive" :size="16" />{{ copy.items.retrieve }}</button></div>
          <div v-else-if="!systemManaged" class="move-block">
            <span class="field-label">{{ copy.items.moveTo }}</span>
            <div><select v-model="moveContainer" class="field-select"><option v-for="container in items.containerNames.filter((name) => name !== 'drop')" :key="container" :value="container">{{ copy.items.containers[container] }}</option></select><select v-model="moveSlot" class="field-select"><option :value="null">{{ copy.items.chooseSlot }}</option><option v-for="slot in moveSlots" :key="slot.SlotIndex" :value="slot.SlotIndex">{{ slotLabel(slot) }} · {{ slot.Item ? itemName(slot.Item) : copy.items.empty }}</option></select><button class="button secondary" type="button" :disabled="moveSlot === null" @click="moveSelected">{{ copy.items.move }}</button></div>
          </div>
          <button v-if="!systemManaged" class="button danger delete-button" type="button" @click="deleteOpen = true"><AppIcon name="trash" :size="16" />{{ copy.items.delete }}</button>
        </template>
        <template v-else-if="selected?.Unlocked && items.selectedContainer !== 'drop'">
          <div class="empty-detail"><span><AppIcon name="plus" :size="28" /></span><h2>{{ copy.items.emptySlot }}</h2><p>{{ copy.items.emptySlotHint }}</p><button class="button primary" type="button" @click="openAdd(selected)">{{ copy.items.addHere }}</button></div>
        </template>
        <template v-else><div class="empty-detail"><span><AppIcon name="box" :size="28" /></span><h2>{{ copy.items.selectItem }}</h2><p>{{ copy.items.selectItemHint }}</p></div></template>
      </aside>
    </section>

    <ModalDialog :open="addOpen" :title="copy.items.addTitle" width="900px" @close="addOpen = false">
      <div class="catalog-filters"><label class="catalog-search"><AppIcon name="search" :size="17" /><input v-model="items.query" :placeholder="copy.items.search" /></label><select v-model="items.category" class="field-select"><option value="">{{ copy.items.allCategories }}</option><option v-for="category in items.categories" :key="category" :value="category">{{ category }}</option></select><select v-model="items.rarity" class="field-select"><option value="">{{ copy.items.allRarities }}</option><option v-for="rarity in [0,1,2,3,4,5]" :key="rarity" :value="String(rarity)">{{ rarityLabel(rarity) }}</option></select></div>
      <div class="add-layout">
        <div class="catalog-list">
          <button v-for="entry in visibleCatalog" :key="entry.StaticId" type="button" :class="{ selected: chosenStaticId === entry.StaticId }" @click="chooseCatalogItem(entry)"><img :src="`/image/items/${entry.IconKey}`" alt="" loading="lazy" /><span><strong>{{ itemName(entry) }}</strong><small>{{ entry.StaticId }}</small></span><StatusPill :tone="entry.Rarity ? 'gold' : 'neutral'">{{ rarityLabel(entry.Rarity) }}</StatusPill></button>
          <p v-if="!visibleCatalog.length" class="catalog-empty">{{ copy.common.noResults }}</p>
        </div>
        <aside class="add-options">
          <template v-if="chosenEntry"><img :src="`/image/items/${chosenEntry.IconKey}`" alt="" loading="lazy" /><h3>{{ itemName(chosenEntry) }}</h3><code>{{ chosenEntry.StaticId }}</code><label v-if="!chosenEntry.DynamicType && chosenEntry.MaxStack !== 1"><span class="field-label">{{ copy.items.quantity }}</span><input v-model.number="addQuantity" class="field-input" type="number" min="1" :max="chosenEntry.MaxStack" /></label><p v-else-if="chosenEntry.MaxStack === 1" class="fixed-quantity">{{ copy.items.fixedQuantity }}</p><label v-if="chosenEntry.DynamicType === 'egg'"><span class="field-label">{{ copy.items.eggSpecies }}</span><SearchableSelect v-model="eggCharacterId" :options="eggSpeciesOptions" :placeholder="copy.items.eggSpecies" :search-placeholder="copy.items.eggSpeciesSearch" :empty-text="copy.common.noResults" /></label><p>{{ copy.items.target }}: {{ copy.items.containers[items.selectedContainer] }} · {{ (items.selectedSlotIndex || 0) + 1 }}</p></template>
          <p v-else>{{ copy.items.chooseItem }}</p>
        </aside>
      </div>
      <template #footer><button class="button secondary" type="button" @click="addOpen = false">{{ copy.common.cancel }}</button><button class="button primary" type="button" :disabled="!chosenEntry || (chosenEntry?.DynamicType === 'egg' && !eggCharacterId)" @click="createItem">{{ copy.items.addHere }}</button></template>
    </ModalDialog>

    <ModalDialog :open="deleteOpen" :title="dangerousDelete ? copy.items.deleteDangerTitle : copy.items.deleteTitle" @close="deleteOpen = false">
      <p class="delete-copy">{{ dangerousDelete ? copy.items.deleteDangerCopy : copy.items.deleteCopy }}</p>
      <template #footer><button class="button secondary" type="button" @click="deleteOpen = false">{{ copy.common.cancel }}</button><button class="button danger" type="button" @click="removeSelected">{{ copy.items.confirmDelete }}</button></template>
    </ModalDialog>
  </AppShell>
</template>

<style scoped>
.items-toolbar{padding:12px 14px;display:flex;align-items:center;gap:16px}.toolbar-field{width:260px}.toolbar-field .field-label{margin-bottom:4px}.toolbar-copy{min-width:0;flex:1}.toolbar-copy strong,.toolbar-copy span{display:block}.toolbar-copy strong{color:var(--text-strong);font-size:15px}.toolbar-copy span{margin-top:3px;color:var(--text-muted);font-size:13px}.container-tabs{margin:12px 0;display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px}.container-tabs button{height:50px;padding:0 11px;display:flex;align-items:center;gap:8px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft);color:var(--text-muted);cursor:pointer}.container-tabs button:hover{border-color:var(--border-bright);color:var(--text)}.container-tabs button.active{border-color:var(--border-violet);background:linear-gradient(135deg,rgba(53,230,209,.1),rgba(139,124,255,.12));color:var(--cyan-200)}.container-tabs span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;font-weight:700}.container-tabs small{margin-left:auto;color:var(--text-faint);font-size:12px}.error-banner{margin:0 0 12px;padding:10px 12px;display:flex;align-items:center;gap:8px;border:1px solid rgba(255,122,138,.26);border-radius:10px;background:rgba(232,91,112,.09);color:var(--red-300);font-size:13px}.inventory-layout{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:12px;align-items:start}.inventory-panel{min-width:0}.slot-grid{padding:12px;display:grid;grid-template-columns:repeat(auto-fill,minmax(104px,1fr));gap:8px}.slot-grid.container-essential{grid-template-columns:repeat(auto-fill,minmax(96px,1fr));max-height:612px;overflow:auto}.slot-grid.container-food,.slot-grid.container-weapon{grid-template-columns:repeat(auto-fill,minmax(112px,1fr))}.slot-grid.container-armor,.slot-grid.container-drop{grid-template-columns:repeat(auto-fill,minmax(128px,1fr))}.item-slot{position:relative;min-width:0;height:116px;padding:19px 8px 8px;display:flex;flex-direction:column;align-items:center;border:1px solid var(--border-subtle);border-radius:10px;background:rgba(5,9,17,.5);color:var(--text-muted);cursor:pointer;overflow:hidden}.item-slot:hover{border-color:var(--border-bright);background:var(--surface-hover);transform:translateY(-1px)}.item-slot.selected{border-color:var(--violet-300);background:var(--surface-selected);box-shadow:0 0 0 2px rgba(139,124,255,.1),inset 0 0 22px rgba(53,230,209,.05)}.item-slot.locked{opacity:.4;cursor:not-allowed}.item-slot.anomalous{border-color:rgba(255,122,138,.4)}.slot-number{position:absolute;top:5px;left:7px;color:var(--text-faint);font-size:12px;font-weight:700}.item-slot img,.unknown-icon{width:46px;height:46px;display:grid;place-items:center;object-fit:contain}.unknown-icon{color:var(--gold-300)}.item-slot strong,.item-slot small{max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.item-slot strong{margin-top:3px;color:var(--text);font-size:13px}.item-slot small{margin-top:1px;color:var(--text-faint);font-size:12px}.item-slot .slot-id{font-size:11px}.item-slot b{position:absolute;right:6px;bottom:6px;padding:2px 5px;border-radius:5px;background:rgba(5,9,17,.88);color:var(--text-strong);font-size:12px}.item-slot i{position:absolute;right:6px;top:5px;width:18px;height:18px;display:grid;place-items:center;border-radius:50%;background:var(--red-400);color:white;font-size:12px;font-style:normal}.empty-mark{margin-top:11px;width:42px;height:42px;display:grid;place-items:center;border:1px dashed var(--border-subtle);border-radius:10px;color:var(--text-faint)}.inventory-empty{padding:64px 20px;display:grid;place-items:center;color:var(--text-muted);font-size:13px}.detail-panel{position:sticky;top:88px;padding:18px}.item-detail-head{display:flex;align-items:center;gap:13px}.item-detail-head>img,.detail-unknown{width:64px;height:64px;display:grid;place-items:center;object-fit:contain;border:1px solid var(--border-subtle);border-radius:13px;background:rgba(255,255,255,.025)}.detail-unknown{color:var(--gold-300)}.item-detail-head>div{min-width:0}.item-detail-head span{color:var(--cyan-300);font-size:12px;font-weight:750}.item-detail-head h2{margin:4px 0 3px;color:var(--text-strong);font-size:18px}.item-detail-head code{display:block;max-width:240px;overflow:hidden;color:var(--text-faint);font-size:11px;text-overflow:ellipsis}.tag-row{margin:14px 0;display:flex;flex-wrap:wrap;gap:7px}.tag-row :deep(.status-pill){min-height:26px;font-size:12px}.state-list{margin-bottom:14px;display:flex;flex-wrap:wrap;gap:5px}.state-list span{padding:4px 7px;border-radius:6px;background:rgba(232,91,112,.1);color:var(--red-300);font-size:12px}.repair-card{margin-bottom:14px;padding:11px;display:flex;align-items:center;gap:10px;border:1px solid rgba(255,122,138,.3);border-radius:10px;background:rgba(255,122,138,.08)}.repair-card>div{min-width:0;flex:1}.repair-card strong,.repair-card span{display:block}.repair-card strong{color:var(--red-300);font-size:13px}.repair-card span{margin-top:3px;color:var(--text-muted);font-size:12px;line-height:1.45}.repair-card .button{flex:0 0 auto;min-height:36px}.detail-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.detail-fields label:only-child{grid-column:1/-1}.egg-card,.passive-card{margin-top:13px;padding:11px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft)}.egg-card{display:flex;align-items:center;gap:10px}.egg-card img{width:44px;height:44px;object-fit:contain}.egg-card span,.passive-card>span{display:block;color:var(--text-faint);font-size:12px}.egg-card strong{display:block;margin-top:3px;color:var(--text);font-size:13px}.passive-card code{display:block;margin-top:5px;color:var(--gold-200);font-size:11px}.move-block{margin-top:16px;padding-top:14px;border-top:1px solid var(--border-subtle)}.move-block>div{display:grid;grid-template-columns:1fr 1fr;gap:7px}.move-block .button{grid-column:1/-1;min-height:40px}.detail-actions{margin-top:16px}.detail-actions .button{width:100%}.delete-button{width:100%;margin-top:9px}.empty-detail{padding:62px 18px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}.empty-detail>span{width:58px;height:58px;display:grid;place-items:center;border:1px solid var(--border-violet);border-radius:14px;background:linear-gradient(145deg,rgba(53,230,209,.08),rgba(139,124,255,.12));color:var(--cyan-300)}.empty-detail h2{margin:14px 0 6px;color:var(--text-strong);font-size:18px}.empty-detail p{max-width:260px;margin:0 0 16px;color:var(--text-muted);font-size:13px;line-height:1.55}.catalog-filters{display:grid;grid-template-columns:minmax(0,1fr) 180px 160px;gap:8px}.catalog-search{height:40px;padding:0 11px;display:flex;align-items:center;gap:8px;border:1px solid var(--border-subtle);border-radius:9px;background:rgba(5,9,17,.58);color:var(--text-faint)}.catalog-search input{width:100%;border:0;outline:0;background:transparent;color:var(--text);font-size:14px}.add-layout{margin-top:12px;display:grid;grid-template-columns:minmax(0,1fr) 240px;gap:12px}.catalog-list{height:440px;padding-right:6px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));align-content:start;gap:7px;overflow:auto}.catalog-list>button{min-width:0;height:74px;padding:9px;display:flex;align-items:center;gap:9px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-soft);color:var(--text);text-align:left;cursor:pointer}.catalog-list>button:hover,.catalog-list>button.selected{border-color:var(--violet-300);background:var(--surface-selected)}.catalog-list img{width:46px;height:46px;flex:0 0 46px;object-fit:contain}.catalog-list button>span{min-width:0;flex:1}.catalog-list strong,.catalog-list small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.catalog-list strong{font-size:13px}.catalog-list small{margin-top:3px;color:var(--text-faint);font-size:11px}.catalog-list :deep(.status-pill){min-height:24px;padding:2px 6px;font-size:12px}.catalog-empty{grid-column:1/-1;padding:80px 0;color:var(--text-muted);font-size:13px;text-align:center}.add-options{padding:15px;border:1px solid var(--border-subtle);border-radius:11px;background:rgba(5,9,17,.45)}.add-options>img{width:80px;height:80px;display:block;margin:0 auto;object-fit:contain}.add-options h3{margin:11px 0 4px;color:var(--text-strong);font-size:15px;text-align:center}.add-options>code{display:block;overflow:hidden;color:var(--text-faint);font-size:11px;text-align:center;text-overflow:ellipsis}.add-options label{display:block;margin-top:16px}.add-options p{margin:18px 0 0;color:var(--text-muted);font-size:13px;line-height:1.55}.add-options .fixed-quantity{margin:16px 0 0;padding:8px;border-radius:8px;background:rgba(53,230,209,.07);color:var(--cyan-300);font-size:12px;text-align:center}.delete-copy{margin:0;color:var(--text-muted);font-size:14px;line-height:1.7}
.system-card{margin-bottom:14px;padding:11px;display:flex;align-items:flex-start;gap:9px;border:1px solid rgba(242,198,109,.28);border-radius:10px;background:rgba(242,198,109,.07);color:var(--gold-300)}.system-card strong,.system-card span{display:block}.system-card strong{font-size:13px}.system-card span{margin-top:3px;color:var(--text-muted);font-size:12px;line-height:1.45}
@media(max-width:1366px){.inventory-layout{grid-template-columns:minmax(0,1fr) 320px}.slot-grid{grid-template-columns:repeat(auto-fill,minmax(96px,1fr))}.slot-grid.container-essential{grid-template-columns:repeat(auto-fill,minmax(90px,1fr))}.item-slot{height:112px}.container-tabs button{padding:0 8px}.container-tabs span{font-size:12px}.toolbar-copy span{display:none}}
</style>
