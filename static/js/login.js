document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  document.getElementById("formError").textContent = "";
  document.getElementById("formSuccess").textContent = "";

  try {
    const response = await fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (!response.ok) {
      document.getElementById("formError").textContent = data.error || "Login failed";
      return;
    }

    document.getElementById("formSuccess").textContent = "Login successful! Redirecting...";
    setTimeout(() => {
      window.location.href = "/";
    }, 500);
  } catch (err) {
    document.getElementById("formError").textContent = "An error occurred. Please try again.";
  }
});