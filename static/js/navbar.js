function checkAuthStatus() {
  const token = getCookie("token");
  const username = getCookie("username");
  
  const registerBtn = document.getElementById("registerBtn");
  const loginBtn = document.getElementById("loginBtn");
  const apiKeysBtn = document.getElementById("apiKeysBtn");
  const logoutBtn = document.getElementById("logoutBtn");

  if (token && username) {
    registerBtn.style.display = "none";
    loginBtn.style.display = "none";
    apiKeysBtn.style.display = "block";
    logoutBtn.style.display = "block";
  } else {
    registerBtn.style.display = "block";
    loginBtn.style.display = "block";
    apiKeysBtn.style.display = "none";
    logoutBtn.style.display = "none";
  }
}

function getCookie(name) {
  const nameEQ = name + "=";
  const cookies = document.cookie.split(';');
  for (let c of cookies) {
    c = c.trim();
    if (c.indexOf(nameEQ) === 0) {
      return c.substring(nameEQ.length);
    }
  }
  return null;
}

function logout() {
  document.cookie = "token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
  document.cookie = "username=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;";
  checkAuthStatus();
  window.location.href = "/";
}

document.addEventListener("DOMContentLoaded", checkAuthStatus);