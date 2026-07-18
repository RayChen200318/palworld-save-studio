export type Locale = 'zh-CN' | 'en'

export interface MockPal {
  id: string
  name: Record<Locale, string>
  icon: string
  level: number
  element: Record<Locale, string>
  gender: 'male' | 'female'
  rank: number
  owner: string
}

export interface SaveSummary {
  name: Record<Locale, string>
  source: 'Steam' | 'Dedicated Server'
  path: string
  worldId: string
  updatedAt: Record<Locale, string>
  players: number
  pals: number
  warnings: number
  backupPath: string
}
