import type { MockPal, SaveSummary } from '@/types/domain'

export const mockSave: SaveSummary = {
  name: { 'zh-CN': 'Ray 的樱岛世界', en: "Ray's Sakurajima World" },
  source: 'Steam',
  path: 'C:\\Users\\Ray\\AppData\\Local\\Pal\\Saved\\SaveGames\\76561198…\\A62F18C9',
  worldId: 'A62F18C9E3144AF5A801F31EC915A2D1',
  updatedAt: { 'zh-CN': '今天 21:48', en: 'Today 21:48' },
  players: 3,
  pals: 186,
  warnings: 1,
  backupPath: 'A62F18C9\\Palworld-Save-Studio-Backup\\2026-07-18_21-48-12',
}

export const mockPals: MockPal[] = [
  { id: 'WorldTreeDragon', name: { 'zh-CN': '枯星龙', en: 'Astralym' }, icon: '/mock/pals/WorldTreeDragon.png', level: 80, element: { 'zh-CN': '龙 / 暗', en: 'Dragon / Dark' }, gender: 'female', rank: 4, owner: 'Ray' },
  { id: 'SamuraiDog', name: { 'zh-CN': '宗铭丸', en: 'Pupperai' }, icon: '/mock/pals/SamuraiDog.png', level: 76, element: { 'zh-CN': '无', en: 'Neutral' }, gender: 'male', rank: 3, owner: 'Ray' },
  { id: 'CloverFairy', name: { 'zh-CN': '幸叶茸', en: 'Clovee' }, icon: '/mock/pals/CloverFairy.png', level: 68, element: { 'zh-CN': '草', en: 'Grass' }, gender: 'female', rank: 2, owner: 'Mori' },
  { id: 'KingWhale', name: { 'zh-CN': '奥沧鲸', en: 'Panthalus' }, icon: '/mock/pals/KingWhale.png', level: 80, element: { 'zh-CN': '水', en: 'Water' }, gender: 'male', rank: 4, owner: 'Ray' },
  { id: 'FlowerPrince', name: { 'zh-CN': '夜蔓爵', en: 'Dandilord' }, icon: '/mock/pals/FlowerPrince.png', level: 71, element: { 'zh-CN': '草 / 暗', en: 'Grass / Dark' }, gender: 'male', rank: 2, owner: 'Yuki' },
  { id: 'CactusDoll', name: { 'zh-CN': '球抱苞', en: 'Needoll' }, icon: '/mock/pals/CactusDoll.png', level: 63, element: { 'zh-CN': '草', en: 'Grass' }, gender: 'female', rank: 1, owner: 'Ray' },
]
