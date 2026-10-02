"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword, 
  signInWithPopup, 
  GoogleAuthProvider 
} from "firebase/auth";

// Import our configuration service manager
import { firebaseAuthService } from "./firebaseConfig";

// Import our refactored secure endpoint sync handlers
import { syncFirebaseSignupWithBackend, syncFirebaseLoginWithBackend } from "../../services/api";

export default function AuthCard() {
  const router = useRouter();

  // Mode and profile configurations
  const [isLogin, setIsLogin] = useState(true);
  const [role, setRole] = useState("student"); // Expects standard: "student" or "teacher"

  // Input text field bindings
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");

  // System loading and message feedback states
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  /**
   * Spawns a secure Firebase pop-up modal allowing users to log in using 
   * their authenticated Google profiles, and hooks into our backend database syncing rules.
   */
  const handleGoogleLogin = async () => {
    setLoading(true);
    setErrorMsg("");
    
    // Initialize the Google credentials provider matrix wrapper
    const provider = new GoogleAuthProvider();

    try {
      const userCredential = await signInWithPopup(firebaseAuthService, provider);
      const uniqueIdToken = await userCredential.user.getIdToken();

      if (isLogin) {
        // --- GOOGLE LOGIN SYNC PATHWAY ---
        const backendSync = await syncFirebaseLoginWithBackend(uniqueIdToken);
        localStorage.setItem("userToken", uniqueIdToken);
        localStorage.setItem("userRole", backendSync.role);

        if (backendSync.role === "teacher") {
          router.push("/teacher");
        } else {
          router.push("/");
        }
      } else {
        // --- GOOGLE SIGNUP SYNC PATHWAY ---
        // For Google popups, extract the display name directly if full name is empty
        const userDisplayName = fullName || userCredential.user.displayName || "Google User";
        
        const backendSync = await syncFirebaseSignupWithBackend({
          idToken: uniqueIdToken,
          fullName: userDisplayName,
          roleSelection: role
        });

        localStorage.setItem("userToken", uniqueIdToken);
        localStorage.setItem("userRole", backendSync.role);

        if (backendSync.role === "teacher") {
          router.push("/teacher");
        } else {
          router.push("/");
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Google federated identity processing failure.");
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");

    try {
      if (isLogin) {
        const userCredential = await signInWithEmailAndPassword(firebaseAuthService, email, password);
        const uniqueIdToken = await userCredential.user.getIdToken();

        const backendSync = await syncFirebaseLoginWithBackend(uniqueIdToken);
        localStorage.setItem("userToken", uniqueIdToken);
        localStorage.setItem("userRole", backendSync.role);

        if (backendSync.role === "teacher") {
          router.push("/teacher");
        } else {
          router.push("/");
        }
      } else {
        const userCredential = await createUserWithEmailAndPassword(firebaseAuthService, email, password);
        const uniqueIdToken = await userCredential.user.getIdToken();

        const backendSync = await syncFirebaseSignupWithBackend({
          idToken: uniqueIdToken,
          fullName: fullName,
          roleSelection: role
        });

        localStorage.setItem("userToken", uniqueIdToken);
        localStorage.setItem("userRole", backendSync.role);

        if (backendSync.role === "teacher") {
          router.push("/teacher");
        } else {
          router.push("/");
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Authentication process failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="authBox">
      <div className="authHeader">
        <h1>{isLogin ? "Welcome Back" : "Create Account"}</h1>
        <p>{isLogin ? "Sign in to your dashboard" : "Register your system access profile"}</p>
      </div>

      {errorMsg && <div className="alertBanner">⚠️ {errorMsg}</div>}

      <form onSubmit={handleFormSubmit} className="authForm">
        {!isLogin && (
          <div className="formGroup">
            <label>Full Name</label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Alex Mercer"
            />
          </div>
        )}

        <div className="formGroup">
          <label>Email Address</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@university.edu"
          />
        </div>

        <div className="formGroup">
          <label>Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
        </div>

        {!isLogin && (
          <div className="formGroup">
            <label>Account Type</label>
            <div className="roleGrid">
              <button
                type="button"
                onClick={() => setRole("student")}
                className={`roleBtn ${role === "student" ? "roleBtnActive" : ""}`}
              >
                🎓 Student
              </button>
              <button
                type="button"
                onClick={() => setRole("teacher")}
                className={`roleBtn ${role === "teacher" ? "roleBtnActive" : ""}`}
              >
                🏫 Faculty
              </button>
            </div>
          </div>
        )}

        <button type="submit" disabled={loading} className="btnMain">
          {loading ? "Verifying..." : isLogin ? "Sign In" : "Register"}
        </button>
      </form>

      {/* ─── VISUAL SEPARATOR LINE DIVIDER ─── */}
      <div className="divider">or</div>

      {/* ─── GOOGLE CALL TO ACTION REGISTRATION ROW BUTTON ─── */}
      <button 
        type="button" 
        disabled={loading} 
        onClick={handleGoogleLogin} 
        className="btnGoogle"
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24" width="16" height="16" xmlns="http://w3.org">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335"/>
        </svg>
        <span>Sign in with Google</span>
      </button>

      <button
        type="button"
        onClick={() => {
          setIsLogin(!isLogin);
          setErrorMsg("");
        }}
        className="toggleLink"
      >
        {isLogin ? "New user? Create an account instead" : "Have an account? Click here to log in"}
      </button>
    </div>
  );
}
