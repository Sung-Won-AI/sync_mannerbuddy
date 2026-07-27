async function requestMannerBuddyAnalysis(text, targetCountry = "JP") {
  return chrome.runtime.sendMessage({
    type: "ANALYZE_EMAIL",
    payload: {
      text,
      target_country: targetCountry,
      language: "en",
      source: "gmail",
      mode: "manual",
      client_request_id: crypto.randomUUID()
    }
  });
}

// Temporary smoke test from the Gmail page console:
window.requestMannerBuddyAnalysis = requestMannerBuddyAnalysis;
