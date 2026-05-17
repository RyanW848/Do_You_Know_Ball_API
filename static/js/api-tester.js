async function callEndpoint(endpoint) {
  let url, method, body, responseId;

  // Map endpoint to responseId first
  switch (endpoint) {
    case "getPlayerId":
      responseId = "playerIdResponse";
      break;
    case "players":
      responseId = "playersResponse";
      break;
    case "stats":
      responseId = "statsResponse";
      break;
    case "teams":
      responseId = "teamsResponse";
      break;
    case "depthchart":
      responseId = "depthchartResponse";
      break;
    case "transactions":
      responseId = "transactionsResponse";
      break;
    case "fakeTransactions":
      responseId = "transactionsResponse";
      break;
    case "value":
      responseId = "valueResponse";
      break;
    default:
      alert("Unknown endpoint");
      return;
  }

  // Check if logged in
  const username = getCookie("username");
  if (!username) {
    showError(responseId, "You must be logged in to test endpoints");
    return;
  }

  let apiKey;
  try {
    const keyResponse = await fetch("/api/user-api-key", {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    });

    if (!keyResponse.ok) {
      showError(
        responseId,
        "Failed to retrieve API key. Have you generated one?",
      );
      return;
    }

    const keyData = await keyResponse.json();
    apiKey = keyData.api_key;
  } catch (err) {
    showError(responseId, "Error fetching API key: " + err.message);
    return;
  }

  // Build URL and body based on endpoint
  switch (endpoint) {
    case "getPlayerId":
      const name = document.getElementById("playerIdName").value;
      const age = document.getElementById("playerIdAge").value;

      if (!name) {
        showError(responseId, "Player name is required");
        return;
      }

      url = `/get-player-id?name=${encodeURIComponent(name)}`;
      if (age) url += `&age=${encodeURIComponent(age)}`;
      method = "GET";
      break;

    case "players":
      url = "/players";
      method = "GET";
      break;

    case "stats":
      const players = document.getElementById("statsPlayers").value;
      const year = document.getElementById("statsYear").value;
      url = "/stats";
      const params = [];
      if (players) params.push(`players=${encodeURIComponent(players)}`);
      if (year) params.push(`year=${encodeURIComponent(year)}`);
      if (params.length) url += "?" + params.join("&");
      method = "GET";
      break;

    case "teams":
      url = "/teams";
      method = "GET";
      break;

    case "depthchart":
      const teamId = document.getElementById("depthchartTeamId").value;
      if (!teamId) {
        showError(responseId, "Team ID is required");
        return;
      }
      url = `/depth-chart?teamId=${encodeURIComponent(teamId)}`;
      method = "GET";
      break;

    case "transactions":
      url = "/transactions";
      method = "GET";
      break;
    case "fakeTransactions":
      url = "/transactions?fake=true";
      method = "GET";
      break;
    case "value":
      const stats = document.getElementById("valueStats").value;
      const budget = document.getElementById("valueBudget").value;
      const playersLeft = document.getElementById("valuePlayersLeft").value;
      const unavailable = document.getElementById("valueUnavailable").value;
      const specificPlayers = document.getElementById("valuePlayers").value;

      url = "/value";
      method = "POST";
      body = {
        relevant_stats: stats || undefined,
        budget: budget ? parseInt(budget) : undefined,
        players_left_to_draft: playersLeft ? parseInt(playersLeft) : undefined,
        unavailable_players: unavailable
          ? unavailable.split(",").map((p) => p.trim())
          : undefined,
        players: specificPlayers
          ? specificPlayers.split(",").map((p) => p.trim())
          : undefined,
      };
      // Remove undefined values
      Object.keys(body).forEach(
        (key) => body[key] === undefined && delete body[key],
      );
      break;
  }

  try {
    const options = {
      method,
      headers: {
        "X-API-Key": apiKey,
        "Content-Type": "application/json",
      },
    };

    if (method === "POST") {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    const data = await response.json();

    showResponse(responseId, response.status, data);
  } catch (err) {
    showError(responseId, err.message);
  }
}

function showResponse(responseId, status, data) {
  const responseDiv = document.getElementById(responseId);
  const responseCode = document.getElementById(responseId + "Code");

  if (!responseDiv || !responseCode) {
    console.error("Response elements not found for:", responseId);
    return;
  }

  const statusClass =
    status >= 200 && status < 300 ? "api-success" : "api-error";

  responseCode.innerHTML = `<span class="${statusClass}">Status: ${status}</span>\n\n${JSON.stringify(data, null, 2)}`;
  responseDiv.style.display = "block";
}

function showError(responseId, message) {
  const responseDiv = document.getElementById(responseId);
  const responseCode = document.getElementById(responseId + "Code");

  if (!responseDiv || !responseCode) {
    console.error("Response elements not found for:", responseId);
    return;
  }

  responseCode.innerHTML = `<span class="api-error">Error: ${message}</span>`;
  responseDiv.style.display = "block";
}

function getCookie(name) {
  const nameEQ = name + "=";
  const cookies = document.cookie.split(";");
  for (let c of cookies) {
    c = c.trim();
    if (c.indexOf(nameEQ) === 0) {
      return c.substring(nameEQ.length);
    }
  }
  return null;
}
