import browser from "webextension-polyfill"

let windowTabHistories: Record<number, number[]> = {}

export async function ensureHistoryInitialized(windowId: number, tabs?: browser.Tabs.Tab[]) {
    if (windowTabHistories[windowId]) return

    const resolvedTabs = tabs || await browser.tabs.query({ windowId })
    if (!resolvedTabs || resolvedTabs.length === 0) return

    const sortedTabs = [...resolvedTabs].sort((a, b) => a.index - b.index)
    const activeTab = sortedTabs.find(t => t.active)
    const history: number[] = []

    if (activeTab && activeTab.id !== undefined) {
        history.push(activeTab.id)
    }

    for (const t of sortedTabs) {
        if (t.id !== undefined && (!activeTab || t.id !== activeTab.id)) {
            history.push(t.id)
        }
    }

    windowTabHistories[windowId] = history
}

export function getHistoryForWindow(windowId: number): number[] {
    return windowTabHistories[windowId] || []
}

export function setHistoryForWindow(windowId: number, history: number[]) {
    windowTabHistories[windowId] = history
}

export async function promoteTabToFront(tabId: number, windowId: number) {
    if (!windowTabHistories[windowId]) {
        await ensureHistoryInitialized(windowId)
    }

    if (windowTabHistories[windowId]) {
        windowTabHistories[windowId] = windowTabHistories[windowId].filter(id => id !== tabId)
        windowTabHistories[windowId].unshift(tabId)
    }
}

export async function addBackgroundTab(tabId: number, windowId: number) {
    if (!windowTabHistories[windowId]) {
        await ensureHistoryInitialized(windowId)
    }

    if (!windowTabHistories[windowId]) {
        windowTabHistories[windowId] = []
    }

    windowTabHistories[windowId] = windowTabHistories[windowId].filter(id => id !== tabId)

    if (windowTabHistories[windowId].length > 0) {
        windowTabHistories[windowId].splice(1, 0, tabId)
    }

    else {
        windowTabHistories[windowId].push(tabId)
    }
}

export function replaceTabId(addedTabId: number, removedTabId: number, windowId: number) {
    if (windowTabHistories[windowId]) {
        windowTabHistories[windowId] = windowTabHistories[windowId].map(id => id === removedTabId ? addedTabId : id)
    }
}

export function removeTabFromHistory(tabId: number, windowId: number) {
    if (windowTabHistories[windowId]) {
        windowTabHistories[windowId] = windowTabHistories[windowId].filter(id => id !== tabId)

        if (windowTabHistories[windowId].length === 0) {
            delete windowTabHistories[windowId]
        }
    }
}

export function removeWindow(windowId: number) {
    delete windowTabHistories[windowId]
}

export async function initializeHistory() {
    try {
        const allWindows = await browser.windows.getAll({ populate: true })

        for (const win of allWindows) {
            if (win.id !== undefined && win.tabs) {
                await ensureHistoryInitialized(win.id, win.tabs)
            }
        }
    }

    catch (err) {
        console.warn(err)
    }
}
