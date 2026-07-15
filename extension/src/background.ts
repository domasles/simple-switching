import browser from "webextension-polyfill"
import * as engine from "./engine"

browser.tabs.onActivated.addListener((activeTab) => {
    if (engine.getIsCycling()) return
    engine.promoteTabToFront(activeTab.tabId)
})

browser.tabs.onCreated.addListener((tab) => {
    if (tab.id !== undefined) {
        engine.addBackgroundTab(tab.id)
    }
})

browser.tabs.onReplaced.addListener((addedTabId, removedTabId) => {
    engine.replaceTabId(addedTabId, removedTabId)
})

browser.tabs.onRemoved.addListener((tabId) => {
    engine.removeTabFromHistory(tabId)
})

engine.initializeHistory()

browser.commands.onCommand.addListener(async (command) => {
    if (command === "switch-tab") {
        await engine.cycleMRUTabs()
    }
})
