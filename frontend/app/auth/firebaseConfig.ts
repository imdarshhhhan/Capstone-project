// Import the functions you need from the SDKs you need
import { initializeApp, getApps } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "",
  authDomain: "adaptive-quiz-platform-29238.firebaseapp.com",
  projectId: "adaptive-quiz-platform-29238",
  storageBucket: "adaptive-quiz-platform-29238.firebasestorage.app",
  messagingSenderId: "249876386382",
  appId: "1:249876386382:web:3a7dc18dcdc60d7887291f",
  measurementId: "G-G7F3THPL9N"
};

// Initialize Firebase
const appInstance = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps();

// EXPLICIT EXPORT: This is the exact variable name AuthCard is looking for!
export const firebaseAuthService = getAuth(appInstance);