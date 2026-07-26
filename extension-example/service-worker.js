const API_BASE_URL = "http://127.0.0.1:8000";

chrome.runtime.onMessage.addListener(async (message) => {
  if (message.type !== "ANALYZE_EMAIL") {
    return undefined;
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/analyses/email`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Extension-Version": chrome.runtime.getManifest().version,
      "X-Request-ID": crypto.randomUUID()
    },
    body: JSON.stringify(message.payload)
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.error?.message ?? "분석 요청에 실패했습니다.");
  }
  return data;
});
