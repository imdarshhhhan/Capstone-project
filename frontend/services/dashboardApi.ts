import { firebaseAuthService } from "@/app/auth/firebaseConfig";
import type { SyncedUser } from "@/services/api";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:8000";

/** An error that remembers the HTTP status, so pages can react to 401/403. */
export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Returns a valid Firebase ID token. Firebase tokens expire after about an
 * hour, so we ask the SDK for a fresh one instead of reusing the copy saved
 * in localStorage at login time.
 */
async function getFreshIdToken(): Promise<string> {
  await firebaseAuthService.authStateReady();
  const user = firebaseAuthService.currentUser;
  if (!user) {
    throw new ApiError("You are signed out. Please sign in again.", 401);
  }
  return user.getIdToken();
}

/** Turns a FastAPI error response into a readable ApiError. */
async function throwApiError(
  response: Response,
  fallbackMessage: string,
): Promise<never> {
  const body = await response.text();
  if (!body) throw new ApiError(fallbackMessage, response.status);

  let parsed: unknown;
  try {
    parsed = JSON.parse(body);
  } catch {
    throw new ApiError(body, response.status);
  }

  if (typeof parsed === "object" && parsed !== null && "detail" in parsed) {
    const { detail } = parsed;
    if (typeof detail === "string") {
      throw new ApiError(detail, response.status);
    }
    // FastAPI validation errors (422) arrive as a list of { msg, loc, ... }.
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) =>
          typeof item === "object" && item !== null && "msg" in item
            ? String(item.msg)
            : null,
        )
        .filter(Boolean);
      if (messages.length > 0) {
        throw new ApiError(messages.join("; "), response.status);
      }
    }
  }
  throw new ApiError(body, response.status);
}

async function authorizedRequest<T>(
  path: string,
  fallbackMessage: string,
  init: { method?: string; body?: unknown } = {},
): Promise<T> {
  const token = await getFreshIdToken();

  let response: Response;
  try {
    response = await fetch(`${BACKEND_URL}${path}`, {
      method: init.method ?? "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        ...(init.body !== undefined ? { "Content-Type": "application/json" } : {}),
      },
      body: init.body !== undefined ? JSON.stringify(init.body) : undefined,
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        `Could not reach the backend at ${BACKEND_URL}. Check that FastAPI is running and FRONTEND_ORIGINS includes this origin.`,
        { cause: error },
      );
    }
    throw error;
  }

  if (!response.ok) await throwApiError(response, fallbackMessage);
  return response.json();
}

// ─── DASHBOARD TYPES ───

export interface TeacherDashboardData {
  profile: SyncedUser;
  stats: {
    materials: number;
    assignments: number;
    questionsInBank: number;
    submissions: number;
  };
  materials: {
    id: number;
    title: string;
    createdAt: string | null;
    questionCount: number;
  }[];
  assignments: {
    id: number;
    title: string;
    materialTitle: string;
    dueDate: string | null;
    submissions: number;
  }[];
}

export type AssignmentStatus = "open" | "completed" | "overdue";

export interface StudentDashboardData {
  profile: SyncedUser;
  stats: {
    openAssignments: number;
    completedAssignments: number;
    averageScorePercent: number | null;
    conceptsTracked: number;
  };
  assignments: {
    id: number;
    title: string;
    materialTitle: string;
    teacherName: string;
    dueDate: string | null;
    status: AssignmentStatus;
    bestScorePercent: number | null;
  }[];
  mastery: {
    conceptTag: string;
    masteryPercent: number;
    lastUpdated: string | null;
  }[];
  recentAttempts: {
    id: number;
    assignmentTitle: string;
    scorePercent: number;
    attemptedAt: string | null;
  }[];
}

// ─── DASHBOARD CALLS ───

export function fetchTeacherDashboard(): Promise<TeacherDashboardData> {
  return authorizedRequest("/dashboard/teacher", "Could not load the dashboard.");
}

export function fetchStudentDashboard(): Promise<StudentDashboardData> {
  return authorizedRequest("/dashboard/student", "Could not load the dashboard.");
}

// These two reuse your existing /documents/upload and /quizzes/assign routes.
export function uploadMaterial(payload: { title: string; textBody: string }) {
  return authorizedRequest<{
    status: string;
    materialId: number;
    title: string;
    chunksIndexed: number;
  }>("/documents/upload", "Document processing failed.", {
    method: "POST",
    body: payload,
  });
}

export function assignHomework(payload: {
  title: string;
  materialId: number;
  dueDate: string; // YYYY-MM-DD
}) {
  return authorizedRequest<{
    status: string;
    assignmentId: number;
    title: string;
    windowClosedAt: string;
  }>("/quizzes/assign", "Could not assign the homework.", {
    method: "POST",
    body: payload,
  });
}   