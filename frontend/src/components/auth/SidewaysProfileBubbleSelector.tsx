"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Briefcase,
  BookOpen,
  HelpCircle,
  ArrowRight,
  ArrowLeft,
  Mail,
  Lock,
  User,
  CheckCircle2,
  Scale,
  Sparkles,
} from "lucide-react";

export type ProfileKey = "lawyer" | "student" | "common";

export interface ProfileItem {
  key: ProfileKey;
  title: string;
  verb: string;
  concept: string;
  description: string;
  route: string;
  features: string[];
  icon: React.ReactNode;
}

export const PROFILE_LIST: ProfileItem[] = [
  {
    key: "lawyer",
    title: "Lawyer",
    verb: "Work",
    concept: "Matter-Centric Workspace",
    description: "Work around your matters, cases, documents, authorities and evidence.",
    route: "/lawyer",
    features: ["Matter timelines", "Authority binders", "Paragraph citations"],
    icon: <Briefcase size={32} />,
  },
  {
    key: "student",
    title: "Student / Researcher",
    verb: "Learn",
    concept: "Knowledge-Centric Workspace",
    description: "Build legal knowledge through questions, cases, notes, bookmarks and research.",
    route: "/student",
    features: ["Jurisprudence notes", "Doctrine bookmarks", "Comparative research"],
    icon: <BookOpen size={32} />,
  },
  {
    key: "common",
    title: "Common Person",
    verb: "Understand",
    concept: "Problem-Centric Workspace",
    description: "Understand legal documents, situation, rights, possible next steps and options.",
    route: "/common",
    features: ["Document interpreter", "Civil rights directory", "Grievance navigation"],
    icon: <HelpCircle size={32} />,
  },
];

export function SidewaysProfileBubbleSelector() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialMode = searchParams.get("mode") === "signin" ? "signin" : "signup";

  const [selectedProfile, setSelectedProfile] = useState<ProfileItem | null>(null);
  const [hoveredKey, setHoveredKey] = useState<ProfileKey | null>(null);
  const [mode, setMode] = useState<"signup" | "signin">(initialMode);

  // Form fields
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (searchParams.get("mode") === "signin") {
      setMode("signin");
    }
  }, [searchParams]);

  const handleSelect = (profile: ProfileItem) => {
    setSelectedProfile(profile);
    setError(null);
  };

  const handleBack = () => {
    setSelectedProfile(null);
    setError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProfile) return;

    if (!email || !password || (mode === "signup" && !name)) {
      setError("Please complete all required fields.");
      return;
    }

    setLoading(true);
    setError(null);

    setTimeout(() => {
      const userData = {
        name: mode === "signup" ? name : email.split("@")[0],
        email,
        profile: selectedProfile.key,
        profileTitle: selectedProfile.title,
        concept: selectedProfile.concept,
        createdAt: "2026-10-08T00:00:00.000Z",
      };

      try {
        localStorage.setItem("vidhik_user", JSON.stringify(userData));
        localStorage.setItem("vidhik_profile", selectedProfile.key);
      } catch (err) {
        console.warn("localStorage unavailable", err);
      }

      setLoading(false);
      router.push(selectedProfile.route);
    }, 600);
  };

  return (
    <div
      style={{
        width: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <AnimatePresence mode="wait">
        {!selectedProfile ? (
          /* =================================================================
             STATE 1: THREE PROMINENT CIRCULAR PROFILE BUBBLES
             ================================================================= */
          <motion.div
            key="bubbles-grid"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.94 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            style={{
              width: "100%",
              maxWidth: "1000px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: "2.75rem",
                width: "100%",
              }}
              className="profile-circles-grid"
            >
              {PROFILE_LIST.map((profile) => {
                const isHovered = hoveredKey === profile.key;

                return (
                  <motion.div
                    key={profile.key}
                    whileHover={{ y: -8 }}
                    transition={{ type: "spring", stiffness: 320, damping: 22 }}
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      cursor: "pointer",
                      textAlign: "center",
                    }}
                    onMouseEnter={() => setHoveredKey(profile.key)}
                    onMouseLeave={() => setHoveredKey(null)}
                    onClick={() => handleSelect(profile)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        handleSelect(profile);
                      }
                    }}
                    aria-label={`Select ${profile.title} workspace`}
                  >
                    {/* Top Verb Pill */}
                    <div
                      style={{
                        padding: "0.22rem 0.75rem",
                        borderRadius: "20px",
                        backgroundColor: isHovered
                          ? "var(--maroon-faint)"
                          : "var(--bg-surface)",
                        border: `1px solid ${
                          isHovered ? "var(--maroon-border)" : "var(--border-rule)"
                        }`,
                        fontSize: "0.72rem",
                        fontFamily: "var(--font-mono)",
                        fontWeight: 700,
                        letterSpacing: "0.12em",
                        textTransform: "uppercase",
                        color: isHovered ? "var(--maroon)" : "var(--text-muted)",
                        marginBottom: "1.25rem",
                        transition: "all 0.2s ease",
                      }}
                    >
                      {profile.verb}
                    </div>

                    {/* Circular Profile Bubble */}
                    <div
                      style={{
                        width: "172px",
                        height: "172px",
                        borderRadius: "50%",
                        backgroundColor: isHovered
                          ? "var(--maroon-faint)"
                          : "var(--bg-sheet)",
                        border: `2.5px solid ${
                          isHovered ? "var(--maroon)" : "var(--border-rule)"
                        }`,
                        boxShadow: isHovered
                          ? "0 12px 32px rgba(110, 31, 42, 0.22), 0 0 0 4px rgba(110, 31, 42, 0.08)"
                          : "0 4px 14px rgba(30, 32, 36, 0.05)",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "0.5rem",
                        transition: "all 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
                        position: "relative",
                      }}
                    >
                      <div
                        style={{
                          color: isHovered ? "var(--maroon)" : "var(--navy)",
                          transition: "all 0.2s ease",
                          transform: isHovered ? "scale(1.15)" : "scale(1)",
                        }}
                      >
                        {profile.icon}
                      </div>

                      <div
                        style={{
                          fontFamily: "var(--font-serif)",
                          fontSize: "1.15rem",
                          fontWeight: 700,
                          color: isHovered ? "var(--maroon)" : "var(--text-ink)",
                          transition: "color 0.2s ease",
                          maxWidth: "130px",
                          lineHeight: 1.2,
                        }}
                      >
                        {profile.title}
                      </div>
                    </div>

                    {/* Supporting concept label */}
                    <div
                      style={{
                        marginTop: "1.5rem",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        gap: "0.35rem",
                        maxWidth: "280px",
                      }}
                    >
                      <span
                        style={{
                          fontFamily: "var(--font-sans)",
                          fontSize: "0.78rem",
                          fontWeight: 700,
                          color: "var(--navy)",
                          letterSpacing: "0.06em",
                          textTransform: "uppercase",
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

                    {/* Select Trigger */}
                    <div
                      style={{
                        marginTop: "1.25rem",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.4rem",
                        padding: "0.45rem 1.15rem",
                        fontSize: "0.82rem",
                        fontWeight: 600,
                        backgroundColor: isHovered
                          ? "var(--maroon)"
                          : "var(--bg-surface)",
                        color: isHovered ? "#FFFFFF" : "var(--text-ink)",
                        border: `1px solid ${
                          isHovered ? "var(--maroon)" : "var(--border-rule)"
                        }`,
                        borderRadius: "2px",
                        boxShadow: isHovered
                          ? "0 2px 8px rgba(110, 31, 42, 0.2)"
                          : "none",
                        transition: "all 0.2s ease",
                      }}
                    >
                      <span>Choose {profile.title}</span>
                      <ArrowRight size={13} />
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        ) : (
          /* =================================================================
             STATE 2: BUBBLE EXPANDS RIGHT SIDEWAYS INTO SPLIT LOGIN/SIGNUP CARD
             ================================================================= */
          <motion.div
            key="sideways-expanded-panel"
            initial={{ opacity: 0, scale: 0.9, x: -30 }}
            animate={{ opacity: 1, scale: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.9, x: 20 }}
            transition={{
              type: "spring",
              damping: 26,
              stiffness: 260,
              duration: 0.55,
            }}
            style={{
              width: "100%",
              maxWidth: "820px",
            }}
          >
            <div
              className="paper-card sideways-expand-container"
              style={{
                backgroundColor: "var(--bg-sheet)",
                border: "2px solid var(--maroon-border)",
                borderRadius: "4px",
                boxShadow: "var(--shadow-modal)",
                overflow: "hidden",
                display: "grid",
                gridTemplateColumns: "280px 1fr",
                minHeight: "460px",
              }}
            >
              {/* Left Anchor: The Profile Bubble Visual Pillar */}
              <div
                style={{
                  backgroundColor: "var(--maroon-faint)",
                  borderRight: "1px solid var(--maroon-border)",
                  padding: "2.5rem 1.75rem",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  alignItems: "center",
                  textAlign: "center",
                }}
              >
                <div>
                  <button
                    onClick={handleBack}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.4rem",
                      fontSize: "0.78rem",
                      fontWeight: 600,
                      color: "var(--text-muted)",
                      backgroundColor: "var(--bg-surface)",
                      border: "1px solid var(--border-rule)",
                      borderRadius: "2px",
                      padding: "0.3rem 0.65rem",
                      cursor: "pointer",
                      marginBottom: "2rem",
                      transition: "all 0.15s ease",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.color = "var(--maroon)";
                      e.currentTarget.style.borderColor = "var(--maroon)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.color = "var(--text-muted)";
                      e.currentTarget.style.borderColor = "var(--border-rule)";
                    }}
                  >
                    <ArrowLeft size={13} />
                    <span>Change Profile</span>
                  </button>

                  {/* Anchored Circular Bubble */}
                  <div
                    style={{
                      width: "110px",
                      height: "110px",
                      borderRadius: "50%",
                      backgroundColor: "var(--bg-sheet)",
                      border: "2.5px solid var(--maroon)",
                      boxShadow: "0 6px 18px rgba(110, 31, 42, 0.15)",
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      margin: "0 auto 1.25rem auto",
                      color: "var(--maroon)",
                    }}
                  >
                    {selectedProfile.icon}
                  </div>

                  <h3
                    style={{
                      fontFamily: "var(--font-serif)",
                      fontSize: "1.4rem",
                      fontWeight: 700,
                      color: "var(--maroon-dark)",
                      marginBottom: "0.35rem",
                    }}
                  >
                    {selectedProfile.title}
                  </h3>

                  <div
                    style={{
                      fontSize: "0.72rem",
                      fontFamily: "var(--font-sans)",
                      fontWeight: 700,
                      color: "var(--navy)",
                      letterSpacing: "0.08em",
                      textTransform: "uppercase",
                      marginBottom: "1rem",
                    }}
                  >
                    {selectedProfile.concept}
                  </div>

                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "0.5rem",
                      textAlign: "left",
                      backgroundColor: "var(--bg-surface)",
                      padding: "0.85rem",
                      borderRadius: "2px",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    {selectedProfile.features.map((feat) => (
                      <div
                        key={feat}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "0.4rem",
                          fontSize: "0.75rem",
                          color: "var(--text-ink)",
                        }}
                      >
                        <CheckCircle2 size={13} color="var(--maroon)" />
                        <span>{feat}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div
                  style={{
                    fontSize: "0.7rem",
                    fontFamily: "var(--font-mono)",
                    color: "var(--text-faint)",
                    letterSpacing: "0.05em",
                    marginTop: "1.5rem",
                  }}
                >
                  VIDHIK IDENTITY ENGINE
                </div>
              </div>

              {/* Right Side: The Form Expanded Sideways */}
              <motion.div
                initial={{ opacity: 0, x: 25 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.45, delay: 0.15 }}
                style={{
                  padding: "2.75rem 2.5rem",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
              >
                <div>
                  {/* Form Header */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: "1.75rem",
                    }}
                  >
                    <div>
                      <h2
                        style={{
                          fontFamily: "var(--font-serif)",
                          fontSize: "1.65rem",
                          fontWeight: 700,
                          color: "var(--text-ink)",
                          marginBottom: "0.25rem",
                        }}
                      >
                        {mode === "signin"
                          ? `Sign in as ${selectedProfile.title}`
                          : `Create ${selectedProfile.title} Workspace`}
                      </h2>
                      <p
                        style={{
                          fontFamily: "var(--font-sans)",
                          fontSize: "0.82rem",
                          color: "var(--text-muted)",
                          margin: 0,
                        }}
                      >
                        {mode === "signin"
                          ? "Enter your credentials to access your personalized research files."
                          : "Set up your verified workspace with evidence-linked intelligence."}
                      </p>
                    </div>
                  </div>

                  {/* Error Notification */}
                  {error && (
                    <div
                      style={{
                        padding: "0.65rem 0.85rem",
                        backgroundColor: "var(--maroon-faint)",
                        border: "1px solid var(--maroon)",
                        borderRadius: "2px",
                        color: "var(--maroon)",
                        fontSize: "0.8rem",
                        marginBottom: "1.25rem",
                      }}
                    >
                      {error}
                    </div>
                  )}

                  {/* Form Inputs */}
                  <form onSubmit={handleSubmit}>
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        gap: "1.1rem",
                      }}
                    >
                      {mode === "signup" && (
                        <div>
                          <label
                            style={{
                              display: "block",
                              fontSize: "0.8rem",
                              fontWeight: 600,
                              color: "var(--text-ink)",
                              marginBottom: "0.35rem",
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
                                padding: "0.7rem 0.85rem 0.7rem 2.3rem",
                                border: "1px solid var(--border-rule)",
                                borderRadius: "2px",
                                backgroundColor: "var(--bg-surface)",
                                fontSize: "0.88rem",
                                color: "var(--text-ink)",
                                outline: "none",
                              }}
                              onFocus={(e) =>
                                (e.currentTarget.style.borderColor = "var(--maroon)")
                              }
                              onBlur={(e) =>
                                (e.currentTarget.style.borderColor = "var(--border-rule)")
                              }
                            />
                            <User
                              size={15}
                              color="var(--text-faint)"
                              style={{
                                position: "absolute",
                                left: "0.8rem",
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
                            fontSize: "0.8rem",
                            fontWeight: 600,
                            color: "var(--text-ink)",
                            marginBottom: "0.35rem",
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
                              padding: "0.7rem 0.85rem 0.7rem 2.3rem",
                              border: "1px solid var(--border-rule)",
                              borderRadius: "2px",
                              backgroundColor: "var(--bg-surface)",
                              fontSize: "0.88rem",
                              color: "var(--text-ink)",
                              outline: "none",
                            }}
                            onFocus={(e) =>
                              (e.currentTarget.style.borderColor = "var(--maroon)")
                            }
                            onBlur={(e) =>
                              (e.currentTarget.style.borderColor = "var(--border-rule)")
                            }
                          />
                          <Mail
                            size={15}
                            color="var(--text-faint)"
                            style={{
                              position: "absolute",
                              left: "0.8rem",
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
                            fontSize: "0.8rem",
                            fontWeight: 600,
                            color: "var(--text-ink)",
                            marginBottom: "0.35rem",
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
                              padding: "0.7rem 0.85rem 0.7rem 2.3rem",
                              border: "1px solid var(--border-rule)",
                              borderRadius: "2px",
                              backgroundColor: "var(--bg-surface)",
                              fontSize: "0.88rem",
                              color: "var(--text-ink)",
                              outline: "none",
                            }}
                            onFocus={(e) =>
                              (e.currentTarget.style.borderColor = "var(--maroon)")
                            }
                            onBlur={(e) =>
                              (e.currentTarget.style.borderColor = "var(--border-rule)")
                            }
                          />
                          <Lock
                            size={15}
                            color="var(--text-faint)"
                            style={{
                              position: "absolute",
                              left: "0.8rem",
                              top: "50%",
                              transform: "translateY(-50%)",
                            }}
                          />
                        </div>
                      </div>

                      <button
                        type="submit"
                        disabled={loading}
                        style={{
                          marginTop: "0.5rem",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          gap: "0.5rem",
                          backgroundColor: "var(--maroon)",
                          color: "#FFFFFF",
                          padding: "0.82rem 1.4rem",
                          borderRadius: "2px",
                          fontSize: "0.92rem",
                          fontWeight: 600,
                          border: "1px solid var(--maroon-dark)",
                          boxShadow: "0 2px 6px rgba(110, 31, 42, 0.25)",
                          cursor: loading ? "wait" : "pointer",
                          opacity: loading ? 0.8 : 1,
                          transition: "all 0.15s ease",
                        }}
                      >
                        {loading ? (
                          <span>Opening {selectedProfile.title} Workspace...</span>
                        ) : (
                          <>
                            <span>
                              {mode === "signin"
                                ? `Log in to ${selectedProfile.title}`
                                : `Enter ${selectedProfile.title} Workspace`}
                            </span>
                            <ArrowRight size={15} />
                          </>
                        )}
                      </button>
                    </div>
                  </form>
                </div>

                {/* Bottom Mode Switcher */}
                <div
                  style={{
                    marginTop: "1.75rem",
                    paddingTop: "1rem",
                    borderTop: "1px solid var(--border-subtle)",
                    textAlign: "center",
                    fontSize: "0.82rem",
                    color: "var(--text-muted)",
                  }}
                >
                  {mode === "signup" ? (
                    <span>
                      Already have an account?{" "}
                      <button
                        type="button"
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
                      Need a workspace account?{" "}
                      <button
                        type="button"
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
                        Create one now
                      </button>
                    </span>
                  )}
                </div>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
