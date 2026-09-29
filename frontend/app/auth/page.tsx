"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { authenticateUser, registerNewUser } from "../../services/api";

export default function AuthGatewayScreen() {
  const router = useRouter();

  // Screen configuration states
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [userRole, setUserRole] = useState("student"); // Default selection

  // Form input field states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");

  // Feedback display states
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  /**
   * Orchestrates the form submissions, calls our API helper hooks,
   * and routes authenticated accounts to their corresponding home bases.
   */
  const handleFormSubmission = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setErrorMessage("");

    try {
      if (isLoginMode) {
        // Run standard login pathway
        const sessionKeys = await authenticateUser({ email, password });
        
        // Save token strings locally in browser storage layers to handle session lockouts
        localStorage.setItem("userToken", sessionKeys.accessToken);
        localStorage.setItem("userRole", sessionKeys.role);
        
        // Push user onto their correct control panels
        if (sessionKeys.role === "teacher") {
          router.push("/teacher");
        } else {
          router.push("/");
        }
      } else {
        // Run signup registration pathway
        const sessionKeys = await registerNewUser({ email, password, fullName, role: userRole });
        
        localStorage.setItem("userToken", sessionKeys.accessToken);
        localStorage.setItem("userRole", sessionKeys.role);

        if (sessionKeys.role === "teacher") {
          router.push("/teacher");
        } else {
          router.push("/");
        }
      }
    } catch (error: any) {
      setErrorMessage(error.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center p-6 text-gray-900">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-3xl p-8 shadow-sm space-y-6">
        
        {/* Title branding text */}
        <div className="text-center">
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">
            {isLoginMode ? "Welcome Back" : "Create Your Account"}
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {isLoginMode ? "Sign in to access your dashboard" : "Get started with adaptive assessment platform tools"}
          </p>
        </div>

        {/* Warning notification dialog card */}
        {errorMessage && (
          <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs font-medium">
            ⚠️ {errorMessage}
          </div>
        )}

        {/* Form Container Element */}
        <form onSubmit={handleFormSubmission} className="space-y-4">
          
          {/* Registration step input requirement */}
          {!isLoginMode && (
            <div className="space-y-1">
              <label className="text-xs font-semibold text-gray-600">Full Name</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Alex Mercer"
                className="w-full p-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
            </div>
          )}

          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-600">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@university.edu"
              className="w-full p-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-600">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full p-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>

          {/* Registration Role Selection Pills */}
          {!isLoginMode && (
            <div className="space-y-1">
              <label className="text-xs font-semibold text-gray-600 block mb-1">Select Account Type</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setUserRole("student")}
                  className={`p-3 border rounded-xl text-sm font-medium transition-all ${userRole === "student" ? "border-blue-500 bg-blue-50 text-blue-700" : "border-gray-200 text-gray-600 hover:bg-gray-50"}`}
                >
                  🎓 Student Account
                </button>
                <button
                  type="button"
                  onClick={() => setUserRole("teacher")}
                  className={`p-3 border rounded-xl text-sm font-medium transition-all ${userRole === "teacher" ? "border-blue-500 bg-blue-50 text-blue-700" : "border-gray-200 text-gray-600 hover:bg-gray-50"}`}
                >
                  🏫 Faculty Account
                </button>
              </div>
            </div>
          )}

          {/* Submission button anchor */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm transition-all disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {loading ? "Verifying Credentials..." : isLoginMode ? "Sign In" : "Register Account"}
          </button>
        </form>

        <hr className="border-gray-100" />

        {/* Dynamic bottom view toggle anchor linkage */}
        <div className="text-center">
          <button
            type="button"
            onClick={() => {
              setIsLoginMode(!isLoginMode);
              setErrorMessage("");
            }}
            className="text-xs font-semibold text-blue-600 hover:underline"
          >
            {isLoginMode ? "New here? Create an account instead" : "Already registered? Click here to sign in"}
          </button>
        </div>

      </div>
    </main>
  );
}
