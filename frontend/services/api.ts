const BACKEND_URL = "http://127.0.0.1:8000";

/**
 * Packs user onboarding data strings and shoots them over to our FastAPI backend.
 * Returns an access token on a successful database insert.
 */
export async function registerNewUser(submitData: any) {
  const response = await fetch(`${BACKEND_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: submitData.email,
      password: submitData.password,
      fullName: submitData.fullName,
      role: submitData.role, // "teacher" or "student"
    }),
  });

  if (!response.ok) {
    const errorLog = await response.json();
    throw new Error(errorLog.detail || "Registration processing failed.");
  }
  return response.json();
}

/**
 * Submits user login inputs to fetch a time-locked security token string.
 */
export async function authenticateUser(loginData: any) {
  const response = await fetch(`${BACKEND_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: loginData.email,
      password: loginData.password,
    }),
  });

  if (!response.ok) {
    const errorLog = await response.json();
    throw new Error(errorLog.detail || "Authentication processing failed.");
  }
  return response.json();
}
