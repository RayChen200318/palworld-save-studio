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

export interface UpdateStatus {
  CurrentVersion: string
  LatestVersion: string | null
  UpdateAvailable: boolean
  ReleaseUrl: string | null
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
  I18n: string
  SortingKey: string | null
  IsHuman: boolean
  IconAccessKey: string
}

export interface PassiveSkill {
  InternalName: string
  I18n: [string, string]
  Rating: number
}

export interface ActiveSkill {
  InternalName: string
  I18n: [string, string]
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
