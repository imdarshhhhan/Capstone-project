const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:8000";

export type UserRole = "student" | "teacher";

export interface SyncedUser {
  userId: number;
  role: UserRole;
  email: string;
  fullName: string;
}

async function fetchBackend(
  url: string,
  init: RequestInit,
): Promise<Response> {
  try {
    return await fetch(url, init);
  } catch (error) {
    if (error instanceof TypeError) {
      const frontendOrigin =
        typeof window === "undefined"
          ? "unknown frontend origin"
          : window.location.origin;
      throw new Error(
        `Could not reach the backend at ${BACKEND_URL} from ${frontendOrigin}. Check that FastAPI is running, the backend URL is reachable from this device, and FRONTEND_ORIGINS includes this frontend origin.`,
        { cause: error },
      );
    }
    throw error;
  }
}

async function throwApiError(
  response: Response,
  fallbackMessage: string,
): Promise<never> {
  const responseBody = await response.text();
  if (!responseBody) {
    throw new Error(fallbackMessage);
  }

  let errorDetails: unknown;
  try {
    errorDetails = JSON.parse(responseBody);
  } catch {
    throw new Error(responseBody);
  }

  if (
    typeof errorDetails === "object" &&
    errorDetails !== null &&
    "detail" in errorDetails &&
    typeof errorDetails.detail === "string"
  ) {
    throw new Error(errorDetails.detail);
  }

  throw new Error(responseBody);
}

export async function syncFirebaseSignupWithBackend(payload: {
  idToken: string;
  fullName: string;
  roleSelection: UserRole;
}): Promise<SyncedUser> {
  const response = await fetchBackend(`${BACKEND_URL}/auth/verify-sync-signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    await throwApiError(
      response,
      "Federated identity signup synchronization failed.",
    );
  }
  return response.json();
}

export async function syncFirebaseLoginWithBackend(
  idToken: string,
): Promise<SyncedUser> {
  const response = await fetchBackend(`${BACKEND_URL}/auth/verify-sync-login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ idToken }),
  });

  if (!response.ok) {
    await throwApiError(
      response,
      "Federated identity login synchronization failed.",
    );
  }
  return response.json();
}

export async function uploadStudyMaterial(
  textContext: string,
  firebaseToken: string,
) {
  const response = await fetchBackend(`${BACKEND_URL}/documents/upload`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${firebaseToken}`,
    },
    body: JSON.stringify({ title: "Lesson Context Notes", textBody: textContext }),
  });

  if (!response.ok) {
    await throwApiError(response, "Document processing failed.");
  }
  return response.json();
}
