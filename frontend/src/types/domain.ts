export type Locale = 'zh-CN' | 'en'

export interface SaveStatistics {
  Players: number
  Pals: number
  Humans: number
  Anomalies: number
  Objects: number
}

export interface CommitResult {
  Verified: boolean
  FilesWritten: number
  BackupPath: string | null
  Revision: number
}

export interface SaveSession {
  Path: string | null
  Loaded: boolean
  DirtyRevision: number
  Dirty: boolean
  Statistics: SaveStatistics
  BackupEnabled: boolean
  BackupPath: string | null
  LastCommit: CommitResult | null
}

export interface SaveConfig {
  I18n: string
  I18nList: Record<string, string>
  Path: string | null
  HasPassword: boolean
  VERSION: string
  IsOfficialBuild: boolean
  BackupEnabled: boolean
}

export type PalObjectType = 'pal' | 'human'
export type PalLocation = 'party' | 'palbox' | 'base' | 'outside'
export type PalSort = 'deck' | 'level' | 'name' | 'owner'

export interface PalSummary {
  InstanceId: string
  CharacterID: string
  SpeciesKey: string
  SpeciesName: string
  NickName: string
  IconAccessKey: string
  PalDeckId: string
  Level: number
  Gender: string | null
  OwnerPlayerUId: string | null
  OwnerName: string | null
  ObjectType: PalObjectType
  Location: PalLocation
  Elements: string[]
  StateFlags: string[]
  IsAnomalous: boolean
}

export interface PalDetail extends PalSummary {
  group_id: string | null
  ContainerId: string | null
  SlotIndex: number | null
  DataAccessKey: string | null
  DisplayName: string
  FriendshipLevel: number
  HasBaseVariant: boolean
  HasBossVariant: boolean
  HasTowerVariant: boolean
  HasWorkerSick: boolean
  IsFaintedPal: boolean
  Is_Unref_Pal: boolean
  in_owner_palbox: boolean
  IsHuman: boolean
  IsBOSS: boolean
  IsRarePal: boolean
  IsTower: boolean
  IsRAID: boolean
  IsPREDATOR: boolean
  IsOilrig: boolean
  IsExpeditionPal: boolean
  IsAwakening: boolean
  ComputedMaxHP: number | null
  ComputedAttack: number | null
  ComputedDefense: number | null
  ComputedCraftSpeed: number | null
  Rank: number
  Rank_HP: number
  Rank_Attack: number
  Rank_Defence: number
  Rank_CraftSpeed: number
  Talent_HP: number
  Talent_Melee: number
  Talent_Shot: number
  Talent_Defense: number
  PassiveSkillList: string[]
  EquipWaza: string[]
  MasteredWaza: string[]
  Suitabilities: Record<string, number>
}

export interface PalCatalogItem {
  InternalName: string
  Elements: string[]
  Invalid: boolean
  Suitabilities: Record<string, number>
  I18n: LocalizedText
  SortingKey: string | null
  IsHuman: boolean
  IconAccessKey: string
}

export interface LocalizedSkillText {
  en: { Name: string; Description: string }
  'zh-CN': { Name: string; Description: string }
}

export interface PassiveSkill {
  InternalName: string
  I18n: LocalizedSkillText
  Rating: number
  IsMutationExclusive: boolean
}

export interface ActiveSkill {
  InternalName: string
  I18n: LocalizedSkillText
  HasSkillFruit: boolean
  IsUniqueSkill: boolean
  Power: number
  Element: string
  CT: number
  Invalid: boolean
}

export interface PlayerSummary {
  PlayerUId: string
  InstanceId: string
  NickName: string
  Level: number
  HasViewingCage: boolean
  OtomoCharacterContainerId: string
  PalStorageContainerId: string
  TechnologyPoint: number
  BossTechnologyPoint: number
  PalCount: number
}

export interface PlayerDetail extends PlayerSummary {
  UnlockedRecipeTechnologyNames: string[]
}

export interface TechnologyItem {
  InternalName: string
  I18n: string
  BossTechnology: boolean
  Level: number
  IconAccessKey: string
}

export interface PathChild {
  filename: string
  isDir: boolean
}

export interface PathContext {
  currentPath: string
  children: Record<string, PathChild>
  isPalDir: boolean
}

export interface PalFilters {
  query: string
  owner: string
  location: string
  element: string
  objectType: string
  anomaly: string
  sort: PalSort
}

export type ItemContainerName = 'common' | 'essential' | 'food' | 'weapon' | 'armor' | 'drop'

export interface LocalizedText {
  en: string
  'zh-CN': string
}

export interface SearchSelectOption {
  value: string
  title: string
  subtitle: string
  meta?: string
  badge?: string
  iconUrl?: string
  searchText: string
}

export interface SearchBrowserOption {
  value: string
  title: string
  subtitle: string
  summary: string
  searchText: string
  badge?: string
  meta?: string
}

export interface ItemCatalogEntry {
  StaticId: string
  BaseKey: string
  I18n: LocalizedText
  Category: string
  TypeA: string
  TypeB: string
  EquipSlot: string | null
  AllowedContainers: ItemContainerName[]
  Rarity: number
  Rank: number
  SortId: number
  MaxStack: number
  DynamicType: 'weapon' | 'armor' | 'egg' | null
  MaxDurability: number
  MagazineSize: number
  IconKey: string
}

export interface ItemCatalogGroup {
  BaseKey: string
  I18n: LocalizedText
  Category: string
  IconKey: string
  Variants: string[]
}

export interface EggSpecies {
  CharacterId: string
  I18n: LocalizedText
  IconAccessKey: string
}

export interface ItemCatalog {
  Source: Record<string, unknown>
  Items: Record<string, ItemCatalogEntry>
  Groups: ItemCatalogGroup[]
  EggSpecies: EggSpecies[]
}

export interface ItemVariantSummary {
  StaticId: string
  Rarity: number
  I18n: LocalizedText
}

export interface ItemSlotItem {
  StaticId: string
  I18n: LocalizedText
  IconKey: string | null
  Category: string
  Quantity: number
  MaxStack: number | null
  Rarity: number | null
  Variants: ItemVariantSummary[]
  DynamicId: string | null
  DynamicType: string | null
  Durability: number | null
  MaxDurability: number | null
  Ammo: number | null
  MagazineSize: number | null
  PassiveSkills: string[]
  EggCharacterId: string | null
  StateFlags: string[]
}

export interface ItemSlot {
  Container: ItemContainerName
  SlotIndex: number
  SlotType: string | null
  Unlocked: boolean
  Item: ItemSlotItem | null
}

export interface PlayerItemContainer {
  ContainerId: string
  Capacity: number
  PhysicalCapacity: number
  UnlockedIndices: number[]
  Slots: ItemSlot[]
  ReadOnlyTarget: boolean
}

export interface PlayerInventory {
  PlayerId: string
  PlayerName: string
  Containers: Record<ItemContainerName, PlayerItemContainer>
}

export interface ItemMutationResult {
  Inventory: PlayerInventory
  DirtyRevision: number
}
