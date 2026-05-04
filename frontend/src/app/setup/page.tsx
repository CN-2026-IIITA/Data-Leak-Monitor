"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Shield, Key, CheckCircle, ArrowRight, Server, ShieldCheck, Copy, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

export default function SetupWizard() {
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [copied, setCopied] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // Check if setup is actually required
    fetch("http://127.0.0.1:8000/api/setup/status")
      .then((res) => res.json())
      .then((data) => {
        if (!data.requires_setup) {
          router.push("/login");
        } else {
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error("Setup check failed", err);
        setLoading(false); // Let them try anyway if API is starting up
      });
  }, [router]);

  const handleSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/setup/initialize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, company_name: companyName }),
      });
      const data = await res.json();
      if (res.ok) {
        setApiKey(data.api_key);
        setStep(3);
      } else {
        alert("Setup failed: " + (data.detail || "Unknown error"));
      }
    } catch (err) {
      alert("Network error. Is the backend running?");
    } finally {
      setSubmitting(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center text-zinc-400">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center relative overflow-hidden font-sans">
      {/* Background glow effects */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-emerald-500/10 blur-[120px] rounded-full pointer-events-none" />
      
      <div className="w-full max-w-md z-10 p-6">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-[#121214]/80 backdrop-blur-xl border border-white/5 p-8 rounded-2xl shadow-2xl"
        >
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="flex flex-col items-center text-center space-y-6"
              >
                <div className="w-16 h-16 bg-emerald-500/10 rounded-2xl flex items-center justify-center border border-emerald-500/20">
                  <ShieldCheck className="w-8 h-8 text-emerald-400" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white mb-2 tracking-tight">Welcome to NetSentinel</h1>
                  <p className="text-zinc-400 text-sm">
                    Your production-grade Data Leak & Network Anomaly Detection system. Let's get your environment configured.
                  </p>
                </div>
                <button
                  onClick={() => setStep(2)}
                  className="w-full py-3 px-4 bg-emerald-500 hover:bg-emerald-600 text-white font-medium rounded-xl transition-all flex items-center justify-center gap-2"
                >
                  Get Started <ArrowRight className="w-4 h-4" />
                </button>
              </motion.div>
            )}

            {step === 2 && (
              <motion.form
                key="step2"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                onSubmit={handleSetup}
                className="space-y-5"
              >
                <div className="text-center mb-6">
                  <h2 className="text-xl font-bold text-white tracking-tight">Create Admin Account</h2>
                  <p className="text-zinc-400 text-xs mt-1">This will be your master login.</p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1.5 block">Organization (Optional)</label>
                    <input
                      type="text"
                      required
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      className="w-full bg-[#0A0A0B] border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all placeholder:text-zinc-600"
                      placeholder="Acme Corp"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1.5 block">Admin Email</label>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full bg-[#0A0A0B] border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all placeholder:text-zinc-600"
                      placeholder="admin@dataleak.com"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1.5 block">Secure Password</label>
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full bg-[#0A0A0B] border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all"
                      placeholder="••••••••"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-3 px-4 bg-emerald-500 hover:bg-emerald-600 text-white font-medium rounded-xl transition-all flex items-center justify-center gap-2 mt-2 disabled:opacity-50"
                >
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Initialize System"}
                </button>
              </motion.form>
            )}

            {step === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center text-center space-y-6"
              >
                <div className="w-16 h-16 bg-emerald-500/10 rounded-2xl flex items-center justify-center border border-emerald-500/20">
                  <CheckCircle className="w-8 h-8 text-emerald-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white mb-2 tracking-tight">System Configured</h2>
                  <p className="text-zinc-400 text-sm">
                    Your local agent needs this secure API key to transmit telemetry.
                  </p>
                </div>

                <div className="w-full bg-[#0A0A0B] border border-emerald-500/20 rounded-xl p-4 relative group">
                  <div className="flex items-center gap-2 mb-2 text-emerald-400/80 text-xs font-medium uppercase">
                    <Key className="w-3 h-3" /> Agent API Key
                  </div>
                  <code className="text-white text-sm break-all font-mono">
                    {apiKey}
                  </code>
                  <button 
                    onClick={copyToClipboard}
                    className="absolute top-4 right-4 p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors border border-white/5 text-zinc-400 hover:text-white"
                  >
                    {copied ? <CheckCircle className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>

                <div className="w-full text-left bg-blue-500/10 border border-blue-500/20 p-4 rounded-xl">
                   <h4 className="text-blue-400 text-xs font-semibold uppercase mb-1 flex items-center gap-2">
                     <Server className="w-3 h-3" /> Next Steps
                   </h4>
                   <ol className="text-blue-200/70 text-xs space-y-1 ml-4 list-decimal">
                     <li>Open <code className="text-blue-300">backend-local-agent/.env</code></li>
                     <li>Paste this key as <code className="text-blue-300">AGENT_API_KEY</code></li>
                     <li>Restart the Local Agent script</li>
                   </ol>
                </div>

                <button
                  onClick={() => router.push("/login")}
                  className="w-full py-3 px-4 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl border border-white/5 transition-all"
                >
                  Proceed to Dashboard
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
}
