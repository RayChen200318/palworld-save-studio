export interface VirtualWindow {
  startRow: number
  endRow: number
  startIndex: number
  endIndex: number
  paddingTop: number
  paddingBottom: number
}

export function computeVirtualWindow(
  itemCount: number,
  columns: number,
  rowHeight: number,
  viewportHeight: number,
  scrollTop: number,
  overscanRows = 4,
): VirtualWindow {
  const safeColumns = Math.max(1, columns)
  const totalRows = Math.ceil(itemCount / safeColumns)
  const firstVisible = Math.max(0, Math.floor(scrollTop / rowHeight))
  const visibleRows = Math.max(1, Math.ceil(viewportHeight / rowHeight))
  const startRow = Math.max(0, firstVisible - overscanRows)
  const endRow = Math.min(totalRows, firstVisible + visibleRows + overscanRows)
  return {
    startRow,
    endRow,
    startIndex: startRow * safeColumns,
    endIndex: Math.min(itemCount, endRow * safeColumns),
    paddingTop: startRow * rowHeight,
    paddingBottom: Math.max(0, (totalRows - endRow) * rowHeight),
  }
}
