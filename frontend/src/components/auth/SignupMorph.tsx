"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Briefcase,
  BookOpen,
  HelpCircle,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Lock,
  Mail,
  User,
  Shield,
  Layers,
} from "lucide-react";

export type ProfileKey = "lawyer" | "student" | "common";

export interface ProfileDefinition {
  key: ProfileKey;
  title: string;
  verb: string;
  concept: string;
  description: string;
  route: string;
  tags: string[];
  cta: string;
  hint: string;
  icon: React.ReactNode;
}

export const PROFILES: ProfileDefinition[] = [
  {
    key: "lawyer",
    title: "Lawyer",
    verb: "Work",
    concept: "Matter-centric workspace",
    description: "Work around your matters, cases, documents, authorities and evidence.",
    route: "/lawyer",
    tags: ["Matter", "Documents", "Timeline", "Research", "Authorities", "Evidence"],
    cta: "Continue as Lawyer",
    hint: "Configures your matter-centric case briefs, authority citation trail, and evidence binders.",
    icon: <Briefcase size={28} />,
  },
  {
    key: "student",
    title: "Student / Researcher",
    verb: "Learn",
    concept: "Knowledge-centric workspace",
    description: "Build your legal knowledge through questions, cases, notes, bookmarks and research.",
    route: "/student",
    tags: ["Questions", "Bookmarks", "Study Points", "Cases", "Topics", "Research"],
    cta: "Continue as Student / Researcher",
    hint: "Initializes your comparative legal research notebooks, doctrine bookmarks, and study dossiers.",
    icon: <BookOpen size={28} />,
  },
  {
    key: "common",
    title: "Common Person",
    verb: "Understand",
    concept: "Problem-centric workspace",
    description: "Understand your legal documents, situation, rights, possible next steps and complaint options.",
    route: "/common",
    tags: ["Problem", "Documents", "Legal Understanding", "Complaint", "Government Authority", "Next Step"],
    cta: "Continue as Common Person",
    hint: "Prepares your plain-language document decoder, civic rights directory, and grievance navigation paths.",
    icon: <HelpCircle size={28} />,
  },
];

export function SignupMorph() {
  const router = useRouter();
  const [selectedProfile, setSelectedProfile] = useState<ProfileDefinition | null>(null);
  const [hoveredProfile, setHoveredProfile] = useState<ProfileKey | null>(null);

  // Form states
  const [mode, setMode] = useState<"signup" | "signin">("signup");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSelectProfile = (profile: ProfileDefinition) => {
    setSelectedProfile(profile);
    setError(null);
  };

  const handleResetProfile = () => {
    setSelectedProfile(null);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProfile) return;

    if (!email || !password || (mode === "signup" && !name)) {
      setError("Please complete all required fields.");
      return;
    }

    setLoading(true);
    setError(null);

    // Simulate account setup & profile persistence
    setTimeout(() => {
      const userData = {
        name: mode === "signup" ? name : email.split("@")[0],
        email,
        profile: selectedProfile.key,
        profileTitle: selectedProfile.title,
        concept: selectedProfile.concept,
        createdAt: new Date().toISOString(),
      };

      try {
        localStorage.setItem("vidhik_user", JSON.stringify(userData));
        localStorage.setItem("vidhik_profile", selectedProfile.key);
      } catch (err) {
        console.warn("Local storage not accessible", err);
      }

      setLoading(false);
      // Route directly to selected workspace placeholder
      router.push(selectedProfile.route);
    }, 750);
  };

  return (
    <div
      style={{
        position: "relative",
        minHeight: "440px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <AnimatePresence mode="wait">
        {!selectedProfile ? (
          /* =================================================================
             INITIAL STATE: THREE CIRCULAR PROFILE NODES
             ================================================================= */
          <motion.div
            key="profile-selection-circles"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.4 }}
            style={{
              width: "100%",
              maxWidth: "1040px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: "2.5rem",
                width: "100%",
              }}
              className="profile-circles-grid"
            >
              {PROFILES.map((profile) => {
                const isHovered = hoveredProfile === profile.key;

                return (
                  <motion.div
                    key={profile.key}
                    whileHover={{ y: -6 }}
                    transition={{ type: "spring", stiffness: 350, damping: 25 }}
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      cursor: "pointer",
                      textAlign: "center",
                    }}
                    onMouseEnter={() => setHoveredProfile(profile.key)}
                    onMouseLeave={() => setHoveredProfile(null)}
                    onClick={() => handleSelectProfile(profile)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        handleSelectProfile(profile);
                      }
                    }}
                    aria-label={`Select ${profile.title} profile workspace`}
                  >
                    {/* Verb Anchor Badge */}
                    <span
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.72rem",
                        fontWeight: 700,
                        letterSpacing: "0.14em",
                        textTransform: "uppercase",
                        color: isHovered ? "var(--maroon)" : "var(--text-faint)",
                        marginBottom: "1rem",
                        transition: "color 0.2s ease",
                      }}
                    >
                      {profile.verb}
                    </span>

                    {/* Circular Profile Node */}
                    <div
                      style={{
                        width: "154px",
                        height: "154px",
                        borderRadius: "50%",
                        backgroundColor: isHovered
                          ? "var(--maroon-faint)"
                          : "var(--bg-sheet)",
                        border: `2px solid ${
                          isHovered ? "var(--maroon)" : "var(--border-rule)"
                        }`,
                        boxShadow: isHovered
                          ? "0 8px 24px rgba(110, 31, 42, 0.18)"
                          : "var(--shadow-sheet)",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "0.4rem",
                        transition: "all 0.25s ease",
                        position: "relative",
                      }}
                    >
                      <div
                        style={{
                          color: isHovered ? "var(--maroon)" : "var(--navy)",
                          transition: "all 0.2s ease",
                          transform: isHovered ? "scale(1.12)" : "scale(1)",
                        }}
                      >
                        {profile.icon}
                      </div>

                      <div
                        style={{
                          fontFamily: "var(--font-serif)",
                          fontSize: "1.05rem",
                          fontWeight: 700,
                          color: isHovered ? "var(--maroon)" : "var(--text-ink)",
                          transition: "color 0.2s ease",
                          maxWidth: "120px",
                          lineHeight: 1.2,
                        }}
                      >
                        {profile.title}
                      </div>
                    </div>

                    {/* Supporting concept label */}
                    <div
                      style={{
                        marginTop: "1.25rem",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        gap: "0.35rem",
                        maxWidth: "260px",
                      }}
                    >
                      <span
                        style={{
                          fontFamily: "var(--font-sans)",
                          fontSize: "0.75rem",
                          fontWeight: 700,
                          color: "var(--navy)",
                          textTransform: "uppercase",
                          letterSpacing: "0.06em",
                        }}
                      >
                        {profile.concept}
                      </span>

                      <p
                        style={{
                          fontFamily: "var(--font-sans)",
                          fontSize: "0.85rem",
                          lineHeight: 1.5,
                          color: "var(--text-muted)",
                          margin: 0,
                        }}
                      >
                        {profile.description}
                      </p>
                    </div>

                    {/* CTA Pill */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectProfile(profile);
                      }}
                      style={{
                        marginTop: "1rem",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.4rem",
                        padding: "0.45rem 1rem",
                        fontSize: "0.8rem",
                        fontWeight: 600,
                        backgroundColor: isHovered
                          ? "var(--maroon)"
                          : "var(--bg-surface)",
                        color: isHovered ? "#FFFFFF" : "var(--navy)",
                        border: `1px solid ${
                          isHovered ? "var(--maroon)" : "var(--border-rule)"
                        }`,
                        borderRadius: "2px",
                        cursor: "pointer",
                        transition: "all 0.2s ease",
                      }}
                    >
                      <span>{profile.cta}</span>
                      <ArrowRight size={13} />
                    </button>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        ) : (
          /* =================================================================
             EXPANDED STATE: HORIZONTAL MORPH INTO SIGNUP PANEL
             ================================================================= */
          <motion.div
            key="signup-panel"
            initial={{ opacity: 0, scale: 0.75, width: "160px" }}
            animate={{ opacity: 1, scale: 1, width: "100%" }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{
              type: "spring",
              damping: 28,
              stiffness: 280,
              duration: 0.6,
            }}
            style={{
              maxWidth: "640px",
              width: "100%",
            }}
          >
            <div
              className="paper-card"
              style={{
                backgroundColor: "var(--bg-sheet)",
                border: "2px solid var(--maroon-border)",
                borderRadius: "4px",
                boxShadow: "var(--shadow-modal)",
                padding: "2.5rem",
                position: "relative",
              }}
            >
              {/* Back to profile selection */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "1.75rem",
                  paddingBottom: "1.25rem",
                  borderBottom: "1px solid var(--border-subtle)",
                }}
              >
                <button
                  onClick={handleResetProfile}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.45rem",
                    fontSize: "0.82rem",
                    fontWeight: 600,
                    color: "var(--text-muted)",
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    padding: "0.3rem 0.5rem",
                    borderRadius: "2px",
                    transition: "color 0.15s ease",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = "var(--maroon)")}
                  onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
                >
                  <ArrowLeft size={15} />
                  <span>← Choose another workspace</span>
                </button>

                {/* Identity Anchor Pill */}
                <div
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    padding: "0.3rem 0.75rem",
                    backgroundColor: "var(--maroon-faint)",
                    border: "1px solid var(--maroon-border)",
                    borderRadius: "2px",
                  }}
                >
                  <span style={{ color: "var(--maroon)" }}>
                    {selectedProfile.icon}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-serif)",
                      fontSize: "0.85rem",
                      fontWeight: 700,
                      color: "var(--maroon)",
                    }}
                  >
                    {selectedProfile.title}
                  </span>
                </div>
              </div>

              {/* Title & Description */}
              <div style={{ marginBottom: "2rem" }}>
                <h3
                  style={{
                    fontFamily: "var(--font-serif)",
                    fontSize: "1.85rem",
                    fontWeight: 700,
                    color: "var(--text-ink)",
                    marginBottom: "0.45rem",
                  }}
                >
                  {mode === "signup"
                    ? "Create your Vidhik workspace"
                    : "Sign in to Vidhik"}
                </h3>

                <p
                  style={{
                    fontFamily: "var(--font-sans)",
                    fontSize: "0.88rem",
                    color: "var(--navy)",
                    fontWeight: 500,
                    marginBottom: "0.5rem",
                  }}
                >
                  {selectedProfile.concept}
                </p>

                <p
                  style={{
                    fontFamily: "var(--font-sans)",
                    fontSize: "0.82rem",
                    lineHeight: 1.5,
                    color: "var(--text-muted)",
                    margin: 0,
                  }}
                >
                  {selectedProfile.hint}
                </p>
              </div>

              {/* Error banner */}
              {error && (
                <div
                  style={{
                    backgroundColor: "var(--maroon-faint)",
                    border: "1px solid var(--maroon)",
                    padding: "0.75rem 1rem",
                    borderRadius: "2px",
                    color: "var(--maroon)",
                    fontSize: "0.82rem",
                    marginBottom: "1.5rem",
                  }}
                >
                  {error}
                </div>
              )}

              {/* Form Inputs */}
              <form onSubmit={handleSubmit}>
                <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                  {mode === "signup" && (
                    <div>
                      <label
                        style={{
                          display: "block",
                          fontFamily: "var(--font-sans)",
                          fontSize: "0.82rem",
                          fontWeight: 600,
                          color: "var(--text-ink)",
                          marginBottom: "0.4rem",
                        }}
                      >
                        Full Name
                      </label>
                      <div style={{ position: "relative" }}>
                        <input
                          type="text"
                          required
                          value={name}
                          onChange={(e) => setName(e.target.value)}
                          placeholder="e.g. Adv. Rajesh Sharma"
                          style={{
                            width: "100%",
                            padding: "0.75rem 0.85rem 0.75rem 2.4rem",
                            border: "1px solid var(--border-rule)",
                            borderRadius: "2px",
                            backgroundColor: "var(--bg-surface)",
                            fontSize: "0.9rem",
                            color: "var(--text-ink)",
                            outline: "none",
                            transition: "border-color 0.15s ease",
                          }}
                          onFocus={(e) => (e.currentTarget.style.borderColor = "var(--maroon)")}
                          onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border-rule)")}
                        />
                        <User
                          size={16}
                          color="var(--text-faint)"
                          style={{
                            position: "absolute",
                            left: "0.85rem",
                            top: "50%",
                            transform: "translateY(-50%)",
                          }}
                        />
                      </div>
                    </div>
                  )}

                  <div>
                    <label
                      style={{
                        display: "block",
                        fontFamily: "var(--font-sans)",
                        fontSize: "0.82rem",
                        fontWeight: 600,
                        color: "var(--text-ink)",
                        marginBottom: "0.4rem",
                      }}
                    >
                      Email Address
                    </label>
                    <div style={{ position: "relative" }}>
                      <input
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="e.g. rajesh@vidhik-law.in"
                        style={{
                          width: "100%",
                          padding: "0.75rem 0.85rem 0.75rem 2.4rem",
                          border: "1px solid var(--border-rule)",
                          borderRadius: "2px",
                          backgroundColor: "var(--bg-surface)",
                          fontSize: "0.9rem",
                          color: "var(--text-ink)",
                          outline: "none",
                          transition: "border-color 0.15s ease",
                        }}
                        onFocus={(e) => (e.currentTarget.style.borderColor = "var(--maroon)")}
                        onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border-rule)")}
                      />
                      <Mail
                        size={16}
                        color="var(--text-faint)"
                        style={{
                          position: "absolute",
                          left: "0.85rem",
                          top: "50%",
                          transform: "translateY(-50%)",
                        }}
                      />
                    </div>
                  </div>

                  <div>
                    <label
                      style={{
                        display: "block",
                        fontFamily: "var(--font-sans)",
                        fontSize: "0.82rem",
                        fontWeight: 600,
                        color: "var(--text-ink)",
                        marginBottom: "0.4rem",
                      }}
                    >
                      Password
                    </label>
                    <div style={{ position: "relative" }}>
                      <input
                        type="password"
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••••••"
                        style={{
                          width: "100%",
                          padding: "0.75rem 0.85rem 0.75rem 2.4rem",
                          border: "1px solid var(--border-rule)",
                          borderRadius: "2px",
                          backgroundColor: "var(--bg-surface)",
                          fontSize: "0.9rem",
                          color: "var(--text-ink)",
                          outline: "none",
                          transition: "border-color 0.15s ease",
                        }}
                        onFocus={(e) => (e.currentTarget.style.borderColor = "var(--maroon)")}
                        onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border-rule)")}
                      />
                      <Lock
                        size={16}
                        color="var(--text-faint)"
                        style={{
                          position: "absolute",
                          left: "0.85rem",
                          top: "50%",
                          transform: "translateY(-50%)",
                        }}
                      />
                    </div>
                  </div>

                  {/* Primary Submit Button */}
                  <button
                    type="submit"
                    disabled={loading}
                    style={{
                      marginTop: "0.75rem",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "0.6rem",
                      backgroundColor: "var(--maroon)",
                      color: "#FFFFFF",
                      padding: "0.88rem 1.5rem",
                      borderRadius: "2px",
                      fontFamily: "var(--font-sans)",
                      fontSize: "0.95rem",
                      fontWeight: 600,
                      border: "1px solid var(--maroon-dark)",
                      boxShadow: "0 2px 6px rgba(110, 31, 42, 0.25)",
                      cursor: loading ? "wait" : "pointer",
                      opacity: loading ? 0.8 : 1,
                      transition: "all 0.15s ease",
                    }}
                  >
                    {loading ? (
                      <span>Initializing Workspace...</span>
                    ) : (
                      <>
                        <span>
                          {mode === "signup"
                            ? `Create ${selectedProfile.title} Workspace`
                            : `Enter ${selectedProfile.title} Workspace`}
                        </span>
                        <ArrowRight size={16} />
                      </>
                    )}
                  </button>
                </div>
              </form>

              {/* Toggle Mode */}
              <div
                style={{
                  marginTop: "1.75rem",
                  textAlign: "center",
                  fontSize: "0.82rem",
                  color: "var(--text-muted)",
                }}
              >
                {mode === "signup" ? (
                  <span>
                    Already have a Vidhik account?{" "}
                    <button
                      onClick={() => setMode("signin")}
                      style={{
                        background: "none",
                        border: "none",
                        color: "var(--maroon)",
                        fontWeight: 600,
                        cursor: "pointer",
                        textDecoration: "underline",
                        padding: 0,
                      }}
                    >
                      Sign in
                    </button>
                  </span>
                ) : (
                  <span>
                    New to Vidhik?{" "}
                    <button
                      onClick={() => setMode("signup")}
                      style={{
                        background: "none",
                        border: "none",
                        color: "var(--maroon)",
                        fontWeight: 600,
                        cursor: "pointer",
                        textDecoration: "underline",
                        padding: 0,
                      }}
                    >
                      Create account
                    </button>
                  </span>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
