/** @odoo-module **/

const REPLACEMENTS = [
    [/OdooBot/g, "CerisBot"],
    [/Odoobot/g, "CerisBot"],
    [/Powered by Odoo/gi, "Powered by CERIS"],
    [/\bOdoo\b/g, "CERIS"],
    [/\bodoo\b/g, "ceris"],
];

const ATTRIBUTES_TO_PATCH = [
    "title",
    "placeholder",
    "alt",
    "aria-label",
    "data-tooltip",
    "data-original-title",
    "value",
];

function replaceBranding(value) {
    if (!value || typeof value !== "string") {
        return value;
    }
    let patched = value;
    for (const [pattern, replacement] of REPLACEMENTS) {
        patched = patched.replace(pattern, replacement);
    }
    return patched;
}

function patchTextNode(node) {
    if (!node || node.nodeType !== Node.TEXT_NODE) {
        return;
    }
    const parentTag = node.parentElement?.tagName;
    if (parentTag === "SCRIPT" || parentTag === "STYLE" || parentTag === "NOSCRIPT") {
        return;
    }
    const patched = replaceBranding(node.nodeValue);
    if (patched !== node.nodeValue) {
        node.nodeValue = patched;
    }
}

function patchAttributes(element) {
    if (!(element instanceof Element)) {
        return;
    }
    for (const attr of ATTRIBUTES_TO_PATCH) {
        if (!element.hasAttribute(attr)) {
            continue;
        }
        const original = element.getAttribute(attr);
        const patched = replaceBranding(original);
        if (patched !== original) {
            element.setAttribute(attr, patched);
        }
    }
}

function patchNodeTree(rootNode) {
    if (!rootNode) {
        return;
    }

    if (rootNode.nodeType === Node.TEXT_NODE) {
        patchTextNode(rootNode);
        return;
    }

    if (!(rootNode instanceof Element) && rootNode !== document) {
        return;
    }

    const startNode = rootNode === document ? document.body : rootNode;
    if (!startNode) {
        return;
    }

    if (startNode instanceof Element) {
        patchAttributes(startNode);
    }

    const textWalker = document.createTreeWalker(startNode, NodeFilter.SHOW_TEXT);
    while (textWalker.nextNode()) {
        patchTextNode(textWalker.currentNode);
    }

    const elementWalker = document.createTreeWalker(startNode, NodeFilter.SHOW_ELEMENT);
    while (elementWalker.nextNode()) {
        patchAttributes(elementWalker.currentNode);
    }
}

function bootCerisRebranding() {
    patchNodeTree(document);

    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            if (mutation.type === "characterData") {
                patchTextNode(mutation.target);
                continue;
            }

            if (mutation.type === "attributes") {
                patchAttributes(mutation.target);
                continue;
            }

            for (const added of mutation.addedNodes) {
                patchNodeTree(added);
            }
        }
    });

    observer.observe(document.documentElement, {
        subtree: true,
        childList: true,
        characterData: true,
        attributes: true,
        attributeFilter: ATTRIBUTES_TO_PATCH,
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootCerisRebranding, { once: true });
} else {
    bootCerisRebranding();
}
