import browser from "webextension-polyfill"
import { CYCLE_DELAY_MS } from "./config"

let frozenHistory: number[] = []
let tabHistory: number[] = []
let cycleIndex = 0

let commitTimeout: ReturnType<typeof setTimeout> | null = null
let isCycling = false

async function saveHistoryToStorage() {
    try {
        if (browser.storage && browser.storage.local) {
            await browser.storage.local.set({ savedTabHistory: tabHistory })
        }
    }

    catch (err) {
        console.warn(err)
    }
}

export function getIsCycling() {
    return isCycling
}

export function promoteTabToFront(tabId: number) {
    tabHistory = tabHistory.filter(id => id !== tabId)
    tabHistory.unshift(tabId)

    saveHistoryToStorage()
}

export function addBackgroundTab(tabId: number) {
    tabHistory = tabHistory.filter(id => id !== tabId)

    if (tabHistory.length > 0) {
        tabHistory.splice(1, 0, tabId)
    }

    else {
        tabHistory.push(tabId)
    }

    saveHistoryToStorage()
}

export function replaceTabId(addedTabId: number, removedTabId: number) {
    tabHistory = tabHistory.map(id => id === removedTabId ? addedTabId : id)
    frozenHistory = frozenHistory.map(id => id === removedTabId ? addedTabId : id)

    saveHistoryToStorage()
}

export function removeTabFromHistory(tabId: number) {
    tabHistory = tabHistory.filter(id => id !== tabId)
    frozenHistory = frozenHistory.filter(id => id !== tabId)

    saveHistoryToStorage()
}

export async function initializeHistory() {
    try {
        const allTabs = await browser.tabs.query({ currentWindow: true })
        const activeIds = new Set(allTabs.map(t => t.id).filter((id): id is number => id !== undefined))

        const activeTab = allTabs.find(t => t.active)
        const activeTabId = activeTab?.id

        let restored: number[] = []

        if (browser.storage && browser.storage.local) {
            const data = await browser.storage.local.get("savedTabHistory") as { savedTabHistory?: number[] }
            restored = data.savedTabHistory || []
        }

        let validRestored = restored.filter(id => activeIds.has(id))

        if (activeTabId !== undefined) {
            validRestored = validRestored.filter(id => id !== activeTabId)
            validRestored.unshift(activeTabId)
        }

        const remainingIds = Array.from(activeIds).filter(id => !validRestored.includes(id))

        tabHistory = [...validRestored, ...remainingIds]
        saveHistoryToStorage()
    }

    catch (err) {
        console.warn(err)
    }
}

export async function cycleMRUTabs() {
    if (commitTimeout) {
        clearTimeout(commitTimeout)
    }

    try {
        const allTabs = await browser.tabs.query({ currentWindow: true })
        const existingTabIds = new Set(allTabs.map(t => t.id).filter((id): id is number => id !== undefined))

        tabHistory = tabHistory.filter(id => id !== undefined && existingTabIds.has(id))

        if (!isCycling) {
            isCycling = true
            cycleIndex = 1
            frozenHistory = [...tabHistory]
        }

        else {
            cycleIndex = (cycleIndex + 1) % frozenHistory.length
        }

        const targetTabId = frozenHistory[cycleIndex]

        if (targetTabId) {
            await browser.tabs.update(targetTabId, { active: true })
        }
    }

    catch (err) {
        console.warn(err)
    }

    commitTimeout = setTimeout(() => {
        commitTabChange()
    }, CYCLE_DELAY_MS)
}

async function commitTabChange() {
    isCycling = false
    commitTimeout = null

    try {
        const activeTabs = await browser.tabs.query({ active: true, currentWindow: true })

        if (activeTabs[0] && activeTabs[0].id !== undefined) {
            promoteTabToFront(activeTabs[0].id)
        }
    }

    catch (err) {
        console.warn(err)
    }
}
