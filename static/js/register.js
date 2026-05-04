document.getElementById("registerForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  document.getElementById("formError").textContent = "";
  document.getElementById("formSuccess").textContent = "";

  try {
    const response = await fetch("/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (!response.ok) {
      document.getElementById("formError").textContent = data.error || "Registration failed";
      return;
    }

    document.getElementById("formSuccess").textContent = "Account created! Redirecting to login...";
    setTimeout(() => {
      window.location.href = "/login";
    }, 500);
  } catch (err) {
    document.getElementById("formError").textContent = "An error occurred. Please try again.";
  }
});