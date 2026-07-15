import browser from "webextension-polyfill"
import { CYCLE_DELAY_MS } from "./config"

let frozenHistory: number[] = []
let tabHistory: number[] = []
let cycleIndex = 0

let commitTimeout: ReturnType<typeof setTimeout> | null = null
let isCycling = false

export function getIsCycling() {
    return isCycling
}

export function promoteTabToFront(tabId: number) {
    tabHistory = tabHistory.filter(id => id !== tabId)
    tabHistory.unshift(tabId)
}

export function removeTabFromHistory(tabId: number) {
    tabHistory = tabHistory.filter(id => id !== tabId)
    frozenHistory = frozenHistory.filter(id => id !== tabId)
}

export function initializeHistory(tabIds: number[]) {
    tabHistory = tabIds
}

export async function cycleMRUTabs() {
    if (commitTimeout) {
        clearTimeout(commitTimeout)
    }

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
        try {
            await browser.tabs.update(targetTabId, { active: true })
        }

        catch (err) {
            console.warn(err)
        }
    }

    commitTimeout = setTimeout(() => {
        commitTabChange()
    }, CYCLE_DELAY_MS)
}

async function commitTabChange() {
    isCycling = false
    commitTimeout = null

    const activeTabs = await browser.tabs.query({ active: true, currentWindow: true })

    if (activeTabs[0] && activeTabs[0].id !== undefined) {
        promoteTabToFront(activeTabs[0].id)
    }
}
