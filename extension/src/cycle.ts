import browser from "webextension-polyfill"

import { CYCLE_DELAY_MS } from "./config"
import * as history from "./history"

let cyclingWindowId: number | null = null
let frozenHistory: number[] = []
let cycleIndex = 0

let cyclingTarget: { tabId: number; windowId: number } | null = null
let commitTimeout: ReturnType<typeof setTimeout> | null = null
let isCycling = false

export function getIsCycling() {
    return isCycling
}

export function handleTabReplaced(addedTabId: number, removedTabId: number, windowId: number) {
    history.replaceTabId(addedTabId, removedTabId, windowId)

    if (cyclingWindowId === windowId) {
        frozenHistory = frozenHistory.map(id => id === removedTabId ? addedTabId : id)
    }
}

export function handleTabRemoved(tabId: number, windowId: number) {
    history.removeTabFromHistory(tabId, windowId)

    if (cyclingWindowId === windowId) {
        frozenHistory = frozenHistory.filter(id => id !== tabId)
    }
}

export function handleWindowRemoved(windowId: number) {
    history.removeWindow(windowId)

    if (cyclingWindowId === windowId) {
        isCycling = false
        cyclingWindowId = null
        frozenHistory = []
    }
}

export async function cycleTabs() {
    if (commitTimeout) {
        clearTimeout(commitTimeout)
    }

    try {
        const currentWindow = await browser.windows.getCurrent()
        const windowId = currentWindow.id

        if (windowId === undefined) return

        const allTabs = await browser.tabs.query({ windowId })
        const existingTabIds = new Set(allTabs.map(t => t.id).filter((id): id is number => id !== undefined))

        await history.ensureHistoryInitialized(windowId, allTabs)

        let currentHistory = history.getHistoryForWindow(windowId).filter(id => existingTabIds.has(id))
        history.setHistoryForWindow(windowId, currentHistory)

        if (currentHistory.length < 2) return

        if (!isCycling || cyclingWindowId !== windowId) {
            isCycling = true
            cyclingWindowId = windowId
            frozenHistory = [...currentHistory]
            cycleIndex = 1
        }

        else {
            cycleIndex = (cycleIndex + 1) % frozenHistory.length
        }

        const targetTabId = frozenHistory[cycleIndex]

        if (targetTabId) {
            cyclingTarget = { tabId: targetTabId, windowId }
            await browser.tabs.update(targetTabId, { active: true })
        }
    }

    catch (err) {
        console.warn(err)
    }

    commitTimeout = setTimeout(() => { commitTabChange() }, CYCLE_DELAY_MS)
}

async function commitTabChange() {
    isCycling = false
    cyclingWindowId = null
    commitTimeout = null

    if (cyclingTarget) {
        await history.promoteTabToFront(cyclingTarget.tabId, cyclingTarget.windowId)
        cyclingTarget = null
    }
}
