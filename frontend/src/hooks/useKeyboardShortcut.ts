// Create src/hooks/useKeyboardShortcut.ts
import { useEffect, useCallback } from 'react'

export const useKeyboardShortcut = (
  shortcut: string, 
  callback: (event: KeyboardEvent) => void,
  options: { preventDefault?: boolean } = { preventDefault: true }
) => {
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    const keys = shortcut.split('+')
    const isCtrl = keys.includes('ctrl') ? event.ctrlKey : true
    const isShift = keys.includes('shift') ? event.shiftKey : true
    const isAlt = keys.includes('alt') ? event.altKey : true
    
    const mainKey = keys[keys.length - 1]
    
    if (isCtrl && isShift && isAlt && event.key.toLowerCase() === mainKey.toLowerCase()) {
      if (options.preventDefault) {
        event.preventDefault()
      }
      callback(event)
    }
  }, [shortcut, callback, options.preventDefault])

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])
}
