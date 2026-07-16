import browser from "webextension-polyfill"

import * as history from "./history"
import * as cycle from "./cycle"

browser.tabs.onActivated.addListener((activeInfo) => {
    if (cycle.getIsCycling()) return

    if (activeInfo.tabId !== undefined && activeInfo.windowId !== undefined) {
        history.promoteTabToFront(activeInfo.tabId, activeInfo.windowId).catch(console.warn)
    }
})

browser.tabs.onCreated.addListener((tab) => {
    if (tab.id !== undefined && tab.windowId !== undefined) {
        history.addBackgroundTab(tab.id, tab.windowId).catch(console.warn)
    }
})

browser.tabs.onReplaced.addListener(async (addedTabId, removedTabId) => {
    try {
        const tab = await browser.tabs.get(addedTabId)

        if (tab.windowId !== undefined) {
            cycle.handleTabReplaced(addedTabId, removedTabId, tab.windowId)
        }
    }

    catch (err) {
        console.warn(err)
    }
})

browser.tabs.onRemoved.addListener((tabId, removeInfo) => {
    if (removeInfo.windowId !== undefined) {
        cycle.handleTabRemoved(tabId, removeInfo.windowId)
    }
})

browser.windows.onRemoved.addListener((windowId) => {
    cycle.handleWindowRemoved(windowId)
})

history.initializeHistory().catch(console.warn)

browser.commands.onCommand.addListener(async (command) => {
    if (command === "switch-tab") {
        await cycle.cycleTabs()
    }
})

browser.alarms.create("keepAlive", { periodInMinutes: 0.5 })

browser.alarms.onAlarm.addListener(async (alarm) => {
    if (alarm.name === "keepAlive") {
        await Promise.resolve()
    }
})
