import { defineStore } from 'pinia'
import { useSessionStore } from './session'

export const useDraftStore = defineStore('draft', {
  state: () => ({
    pendingRequests: 0,
    error: '',
  }),
  getters: {
    pending: (state) => state.pendingRequests > 0,
    canCommit(state): boolean {
      return useSessionStore().dirty && state.pendingRequests === 0
    },
  },
  actions: {
    async runMutation<T>(operation: () => Promise<T>): Promise<T> {
      this.pendingRequests += 1
      this.error = ''
      try {
        return await operation()
      } catch (error) {
        this.error = error instanceof Error ? error.message : String(error)
        throw error
      } finally {
        this.pendingRequests -= 1
      }
    },
    clearError() {
      this.error = ''
    },
  },
})
