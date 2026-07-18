<script setup lang="ts">
defineProps<{ name: string; size?: number }>()
</script>

<template>
  <svg
    class="app-icon"
    :width="size || 20"
    :height="size || 20"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <g stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <template v-if="name === 'grid'">
        <rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>
      </template>
      <template v-else-if="name === 'users'">
        <circle cx="9" cy="8" r="3"/><path d="M3.5 19c.4-3.3 2.2-5 5.5-5s5.1 1.7 5.5 5"/><path d="M15.5 5.5a3 3 0 0 1 0 5.8M16 14c2.8.2 4.3 1.9 4.5 5"/>
      </template>
      <template v-else-if="name === 'paw'">
        <ellipse cx="12" cy="15.5" rx="5.2" ry="4.2"/><ellipse cx="5.7" cy="10" rx="2" ry="2.5" transform="rotate(-20 5.7 10)"/><ellipse cx="10.3" cy="7" rx="2" ry="2.5"/><ellipse cx="15.3" cy="7.5" rx="2" ry="2.5" transform="rotate(8 15.3 7.5)"/><ellipse cx="19" cy="11" rx="2" ry="2.5" transform="rotate(22 19 11)"/>
      </template>
      <template v-else-if="name === 'settings'">
        <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3v-.2h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"/>
      </template>
      <template v-else-if="name === 'folder'">
        <path d="M3 6.5h6l2 2h10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-11Z"/><path d="M3 10h18"/>
      </template>
      <template v-else-if="name === 'shield'">
        <path d="M12 3 20 6v5.2c0 4.8-3.2 8.3-8 9.8-4.8-1.5-8-5-8-9.8V6l8-3Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/>
      </template>
      <template v-else-if="name === 'search'">
        <circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>
      </template>
      <template v-else-if="name === 'arrow-right'">
        <path d="M5 12h14M14 7l5 5-5 5"/>
      </template>
      <template v-else-if="name === 'arrow-left'">
        <path d="M19 12H5M10 7l-5 5 5 5"/>
      </template>
      <template v-else-if="name === 'check'">
        <path d="m5 12 4 4L19 6"/>
      </template>
      <template v-else-if="name === 'alert'">
        <path d="M12 3 2.8 20h18.4L12 3Z"/><path d="M12 9v4.5M12 17h.01"/>
      </template>
      <template v-else-if="name === 'save'">
        <path d="M4 3h13l3 3v15H4V3Z"/><path d="M8 3v6h8V3M8 21v-7h8v7"/>
      </template>
      <template v-else-if="name === 'copy'">
        <rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/>
      </template>
      <template v-else-if="name === 'trash'">
        <path d="M4 7h16M9 7V4h6v3M7 7l1 14h8l1-14M10 11v6M14 11v6"/>
      </template>
      <template v-else-if="name === 'heart'">
        <path d="M20.8 8.4c0 5-8.8 10.6-8.8 10.6S3.2 13.4 3.2 8.4A4.4 4.4 0 0 1 12 8a4.4 4.4 0 0 1 8.8.4Z"/>
      </template>
      <template v-else-if="name === 'archive'">
        <path d="M4 8h16v12H4V8ZM3 4h18v4H3V4ZM9 12h6"/>
      </template>
      <template v-else-if="name === 'external'">
        <path d="M14 4h6v6M20 4l-9 9"/><path d="M20 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h5"/>
      </template>
      <template v-else-if="name === 'chevron'">
        <path d="m9 5 7 7-7 7"/>
      </template>
      <template v-else-if="name === 'spark'">
        <path d="m12 3 1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5L12 3Z"/><path d="m19 16 .6 2.4L22 19l-2.4.6L19 22l-.6-2.4L16 19l2.4-.6L19 16Z"/>
      </template>
      <template v-else-if="name === 'file'">
        <path d="M6 3h8l4 4v14H6V3Z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>
      </template>
      <template v-else-if="name === 'server'">
        <rect x="3" y="4" width="18" height="6" rx="2"/><rect x="3" y="14" width="18" height="6" rx="2"/><path d="M7 7h.01M7 17h.01M11 7h6M11 17h6"/>
      </template>
      <template v-else>
        <circle cx="12" cy="12" r="8"/><path d="M12 8v4M12 16h.01"/>
      </template>
    </g>
  </svg>
</template>
