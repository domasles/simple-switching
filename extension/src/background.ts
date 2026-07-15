import browser from "webextension-polyfill"
import * as engine from "./engine"

browser.tabs.onActivated.addListener((activeTab) => {
    if (engine.getIsCycling()) return
    engine.promoteTabToFront(activeTab.tabId)
})

browser.tabs.onRemoved.addListener((tabId) => {
    engine.removeTabFromHistory(tabId)
})

browser.tabs.query({ currentWindow: true }).then((tabs) => {
    const ids = tabs.map(t => t.id).filter((id): id is number => id !== undefined)
    engine.initializeHistory(ids)
})

browser.commands.onCommand.addListener(async (command) => {
    if (command === "switch-tab") {
        await engine.cycleMRUTabs()
    }
})
