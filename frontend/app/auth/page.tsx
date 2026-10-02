import React from "react";
import AuthCard from "./AuthCard";
import "./auth.css"; // Imports the local short-class stylesheet

export default function AuthPage() {
  return (
    <main className="authContainer">
      <AuthCard />
    </main>
  );
}
