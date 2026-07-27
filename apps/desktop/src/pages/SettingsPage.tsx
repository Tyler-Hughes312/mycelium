import { useCallback, useEffect, useState } from "react";
import {
  clearImpactEvents,
  disconnectGitHub,
  getGitHubStatus,
  getImpactPricing,
  getSettings,
  patchSettings,
  pollGitHubDevice,
  saveGitHubPat,
  startGitHubDevice,
  type AppSettings,
  type EmbeddingStatus,
  type GitHubStatus,
  type ImpactPricing,
} from "../api/client";

/** Shipped Core defaults — keep in sync with `DEFAULT_INPUT_RATES_USD_PER_1M`. */
const SHIPPED_INPUT_RATES: Record<string, number> = {
  "claude-sonnet-4": 3.0,
  "claude-opus-4": 15.0,
  "claude-haiku-3.5": 0.8,
  "gpt-4o": 2.5,
  "gpt-4.1": 2.0,
  "gemini-2.5-flash": 0.15,
  "gemini-2.5-pro": 1.25,
};

function diffImpactPricingOverrides(
  draft: Record<string, number>,
): Record<string, number> {
  const overrides: Record<string, number> = {};
  for (const [id, value] of Object.entries(draft)) {
    const shipped = SHIPPED_INPUT_RATES[id];
    if (shipped === undefined || Math.abs(value - shipped) > 1e-9) {
      overrides[id] = value;
    }
  }
  return overrides;
}

const MODEL_OPTIONS = [
  {
    id: "sentence-transformers/all-MiniLM-L6-v2",
    name: "MiniLM L6",
    badge: "Recommended",
    blurb: "Best default — fast, solid semantic recall for code + notes.",
    detail: "Small local model · ships as Mycelium default",
  },
  {
    id: "jinaai/jina-embeddings-v2-base-code",
    name: "Jina Code v2",
    badge: "Code-first",
    blurb: "Stronger on source and identifiers; larger download and slower index.",
    detail: "Code-specialized · heavier on disk/CPU",
  },
  {
    id: "mycelium-hashing-v1",
    name: "Hashing (dev)",
    badge: "Tests only",
    blurb: "No neural model — fine for CI, weak for real search.",
    detail: "Offline stub · not for daily indexing",
  },
] as const;

export function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [runtime, setRuntime] = useState<Partial<EmbeddingStatus>>({});
  const [vaultDir, setVaultDir] = useState("");
  const [historyDepth, setHistoryDepth] = useState(500);
  const [model, setModel] = useState<string>(MODEL_OPTIONS[0].id);
  const [githubClientId, setGithubClientId] = useState("");
  const [impactTracking, setImpactTracking] = useState(true);
  const [impactPricing, setImpactPricing] = useState<ImpactPricing | null>(null);
  const [impactDefaultModel, setImpactDefaultModel] = useState("claude-sonnet-4");
  const [impactRates, setImpactRates] = useState<Record<string, number>>({});
  const [allowRemoteLlm, setAllowRemoteLlm] = useState(false);
  const [llmBaseUrl, setLlmBaseUrl] = useState("https://api.openai.com/v1");
  const [llmModel, setLlmModel] = useState("gpt-4o-mini");
  const [llmApiKey, setLlmApiKey] = useState("");
  const [llmKeyConfigured, setLlmKeyConfigured] = useState(false);
  const [llmKeyEnv, setLlmKeyEnv] = useState("MYCELIUM_LLM_API_KEY");
  const [savingLlm, setSavingLlm] = useState(false);
  const [github, setGithub] = useState<GitHubStatus | null>(null);
  const [pat, setPat] = useState("");
  const [deviceCode, setDeviceCode] = useState<string | null>(null);
  const [deviceUri, setDeviceUri] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savingImpact, setSavingImpact] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const applyImpactPricingDraft = useCallback((pricing: ImpactPricing) => {
    setImpactPricing(pricing);
    setImpactDefaultModel(pricing.default_model);
    setImpactRates(
      Object.fromEntries(
        pricing.rates.map((rate) => [rate.id, rate.usd_per_1m_input]),
      ),
    );
  }, []);

  const refreshGitHub = useCallback(async () => {
    const status = await getGitHubStatus();
    setGithub(status);
    return status;
  }, []);

  useEffect(() => {
    void Promise.all([getSettings(), getImpactPricing()])
      .then(async ([data, pricing]) => {
        setSettings(data.settings);
        setRuntime(data.embedding_runtime as Partial<EmbeddingStatus>);
        setVaultDir(data.settings.vault_dir);
        setHistoryDepth(data.settings.history_depth);
        setModel(data.settings.embedding_model);
        setGithubClientId(data.settings.github_client_id ?? "");
        setImpactTracking(data.settings.impact_tracking_enabled !== false);
        setAllowRemoteLlm(data.settings.allow_remote_llm === true);
        setLlmBaseUrl(data.settings.llm_base_url ?? "https://api.openai.com/v1");
        setLlmModel(data.settings.llm_model ?? "gpt-4o-mini");
        setLlmKeyConfigured(data.settings.llm_api_key_configured === true);
        setLlmKeyEnv(data.settings.llm_api_key_env ?? "MYCELIUM_LLM_API_KEY");
        applyImpactPricingDraft(pricing);
        if (data.github) setGithub(data.github);
        else await refreshGitHub();
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load settings");
      });
  }, [applyImpactPricingDraft, refreshGitHub]);

  async function onApply() {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const res = await patchSettings({
        vault_dir: vaultDir,
        history_depth: historyDepth,
        embedding_model: model,
        github_client_id: githubClientId,
        impact_tracking_enabled: impactTracking,
      });
      setSettings(res.settings);
      if (res.github) setGithub(res.github);
      setMessage(res.restart_hint ?? "Settings saved.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function onSavePat() {
    setError(null);
    setMessage(null);
    try {
      const res = await saveGitHubPat(pat);
      setPat("");
      setMessage(`Connected as @${res.login}`);
      await refreshGitHub();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "PAT save failed");
    }
  }

  async function onDeviceStart() {
    setError(null);
    setMessage(null);
    try {
      // Persist client_id so Core can run device flow
      if (githubClientId.trim()) {
        const saved = await patchSettings({ github_client_id: githubClientId });
        setSettings(saved.settings);
        if (saved.github) setGithub(saved.github);
      }
      const start = await startGitHubDevice();
      setDeviceCode(start.user_code);
      setDeviceUri(start.verification_uri);
      setPolling(true);
      const intervalMs = Math.max(5, start.interval || 5) * 1000;
      const deadline = Date.now() + (start.expires_in || 900) * 1000;
      while (Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, intervalMs));
        const poll = await pollGitHubDevice();
        if (poll.status === "connected") {
          setDeviceCode(null);
          setDeviceUri(null);
          setMessage(`Connected as @${poll.login}`);
          await refreshGitHub();
          break;
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Device login failed");
    } finally {
      setPolling(false);
    }
  }

  async function onDisconnect() {
    setError(null);
    await disconnectGitHub();
    setMessage("GitHub disconnected");
    await refreshGitHub();
  }

  async function onSaveLlm() {
    setSavingLlm(true);
    setError(null);
    setMessage(null);
    try {
      const payload: Parameters<typeof patchSettings>[0] = {
        allow_remote_llm: allowRemoteLlm,
        llm_base_url: llmBaseUrl.trim() || "https://api.openai.com/v1",
        llm_model: llmModel.trim() || "gpt-4o-mini",
      };
      if (llmApiKey.trim()) {
        payload.llm_api_key = llmApiKey.trim();
      }
      const res = await patchSettings(payload);
      setSettings(res.settings);
      setAllowRemoteLlm(res.settings.allow_remote_llm === true);
      setLlmBaseUrl(res.settings.llm_base_url ?? llmBaseUrl);
      setLlmModel(res.settings.llm_model ?? llmModel);
      setLlmKeyConfigured(res.settings.llm_api_key_configured === true);
      setLlmKeyEnv(res.settings.llm_api_key_env ?? "MYCELIUM_LLM_API_KEY");
      setLlmApiKey("");
      setMessage("Chat LLM settings saved.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Chat LLM save failed");
    } finally {
      setSavingLlm(false);
    }
  }

  async function onSaveImpactPricing() {
    setSavingImpact(true);
    setError(null);
    setMessage(null);
    try {
      const res = await patchSettings({
        impact_default_model: impactDefaultModel,
        impact_pricing_overrides: diffImpactPricingOverrides(impactRates),
      });
      setSettings(res.settings);
      applyImpactPricingDraft(await getImpactPricing());
      setMessage("Impact pricing saved.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Impact pricing save failed");
    } finally {
      setSavingImpact(false);
    }
  }

  async function onResetImpactPricing() {
    setSavingImpact(true);
    setError(null);
    setMessage(null);
    try {
      const res = await patchSettings({
        impact_pricing_overrides: {},
        impact_default_model: "claude-sonnet-4",
      });
      setSettings(res.settings);
      applyImpactPricingDraft(await getImpactPricing());
      setMessage("Impact pricing reset to defaults.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Impact pricing reset failed");
    } finally {
      setSavingImpact(false);
    }
  }

  return (
    <div className="h-full overflow-y-auto p-xl scroll-smooth bg-surface">
      <div className="max-w-3xl mx-auto space-y-xl pb-xxl">
        <div className="mb-lg">
          <h1 className="font-headline-lg text-headline-lg text-foreground mb-xs">
            Local Environment Setup
          </h1>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Configure core storage paths and embedded intelligence parameters.
          </p>
        </div>

        <section className="border border-border bg-surface-container-low rounded-lg p-lg flex items-start gap-md">
          <div className="mt-xs">
            <span
              className="material-symbols-outlined text-outline text-[24px]"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              lock
            </span>
          </div>
          <div>
            <h2 className="font-label-md text-label-md text-on-surface mb-xs flex items-center gap-xs">
              Stays on this machine
              <span className="w-2 h-2 rounded-full bg-primary" />
            </h2>
            <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
              {settings?.privacy.summary ??
                "Mycelium operates entirely local-first. No cloud account is required."}
            </p>
            <p className="font-technical-mono-sm text-technical-mono-sm text-muted mt-2">
              allow_code_upload={String(settings?.allow_code_upload ?? false)} ·
              allow_remote_llm={String(allowRemoteLlm)} ·
              impact_tracking={String(impactTracking)} ·
              api_token={settings?.api_token_enabled ? "on" : "off"} ·
              config_version={settings?.config_version ?? "—"}
            </p>
            <div className="mt-md flex flex-col gap-sm sm:flex-row sm:items-center sm:justify-between">
              <label className="flex items-center gap-sm font-body-sm text-body-sm text-on-surface cursor-pointer">
                <input
                  type="checkbox"
                  checked={impactTracking}
                  onChange={(e) => setImpactTracking(e.target.checked)}
                  className="accent-[var(--color-primary,#00d1b2)]"
                />
                Track local impact estimates (search / focus / vault pack)
              </label>
              <button
                type="button"
                onClick={() => {
                  if (
                    !window.confirm(
                      "Clear all local impact history on this machine?",
                    )
                  ) {
                    return;
                  }
                  void clearImpactEvents()
                    .then(() => setMessage("Impact history cleared."))
                    .catch((err: unknown) => {
                      setError(
                        err instanceof Error
                          ? err.message
                          : "Failed to clear impact history",
                      );
                    });
                }}
                className="px-md h-9 rounded-lg border border-border font-label-md text-label-md self-start"
              >
                Clear impact history
              </button>
            </div>

            {impactPricing && (
              <div className="mt-lg space-y-md border-t border-border pt-md">
                <div>
                  <p className="font-label-md text-label-md text-on-surface">
                    Impact cost estimates
                  </p>
                  <p className="font-body-sm text-body-sm text-on-surface-variant mt-xs leading-relaxed">
                    {impactPricing.disclaimer}
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-md items-start">
                  <div className="md:col-span-1 pt-sm">
                    <label
                      htmlFor="impact-default-model"
                      className="font-label-md text-label-md text-foreground block"
                    >
                      Default model
                    </label>
                  </div>
                  <div className="md:col-span-3">
                    <select
                      id="impact-default-model"
                      className="w-full max-w-md bg-surface-container border border-border rounded-lg h-10 px-md font-technical-mono text-technical-mono text-foreground focus:outline-none focus:border-primary"
                      value={impactDefaultModel}
                      onChange={(e) => setImpactDefaultModel(e.target.value)}
                    >
                      {impactPricing.rates.map((rate) => (
                        <option key={rate.id} value={rate.id}>
                          {rate.id}
                        </option>
                      ))}
                    </select>
                    <p className="font-technical-mono-sm text-technical-mono-sm text-muted mt-xs">
                      Used when MCP does not send a model id (labeled Assumed on
                      Impact).
                    </p>
                  </div>
                </div>

                <div className="space-y-sm">
                  <p className="font-label-md text-label-md text-foreground">
                    API list prices ($ / 1M input tokens)
                  </p>
                  {impactPricing.rates.map((rate) => (
                    <div
                      key={rate.id}
                      className="grid grid-cols-1 md:grid-cols-4 gap-md items-center"
                    >
                      <div className="md:col-span-1 flex flex-wrap items-center gap-sm">
                        <span className="font-technical-mono-sm text-technical-mono-sm text-on-surface">
                          {rate.id}
                        </span>
                        {rate.overridden ? (
                          <span className="font-label-caps text-label-caps text-primary uppercase tracking-wider">
                            overridden
                          </span>
                        ) : null}
                      </div>
                      <div className="md:col-span-3 flex items-center gap-sm">
                        <span className="font-body-sm text-body-sm text-muted">$</span>
                        <input
                          type="number"
                          min={0}
                          step={0.01}
                          aria-label={`${rate.id} USD per 1M input tokens`}
                          className="w-32 bg-surface-container border border-border rounded-lg h-10 px-sm font-technical-mono text-technical-mono text-foreground text-center focus:outline-none focus:border-primary"
                          value={impactRates[rate.id] ?? rate.usd_per_1m_input}
                          onChange={(e) => {
                            const next = parseFloat(e.target.value);
                            setImpactRates((prev) => ({
                              ...prev,
                              [rate.id]: Number.isFinite(next) ? next : 0,
                            }));
                          }}
                        />
                        <span className="font-body-sm text-body-sm text-muted">
                          / 1M input
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex flex-wrap gap-sm justify-end pt-sm">
                  <button
                    type="button"
                    disabled={savingImpact}
                    onClick={() => void onResetImpactPricing()}
                    className="px-md h-9 rounded-lg border border-border font-label-md text-label-md disabled:opacity-50"
                  >
                    Reset defaults
                  </button>
                  <button
                    type="button"
                    disabled={savingImpact}
                    onClick={() => void onSaveImpactPricing()}
                    className="px-md h-9 rounded-xl bg-primary text-on-primary font-label-md text-label-md disabled:opacity-50"
                  >
                    {savingImpact ? "Saving…" : "Save pricing"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>

        {error && (
          <p className="font-body-sm text-body-sm text-danger">{error}</p>
        )}
        {message && (
          <p className="font-body-sm text-body-sm text-primary">{message}</p>
        )}

        <section className="space-y-lg">
          <h3 className="font-label-caps text-label-caps text-on-surface-variant border-b border-border pb-xs uppercase tracking-widest">
            Mycelium Chat LLM
          </h3>
          <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
            Opt-in remote completions for Desktop Chat. Each turn uses a RAG
            window (prefs + recent tail + ranked hits) — never the full
            transcript. Cursor&apos;s conversation window is not rewritten.
          </p>

          <label className="flex items-start gap-sm font-body-sm text-body-sm text-on-surface cursor-pointer">
            <input
              type="checkbox"
              checked={allowRemoteLlm}
              onChange={(e) => setAllowRemoteLlm(e.target.checked)}
              className="mt-0.5 accent-[var(--color-primary,#00d1b2)]"
            />
            <span>
              <span className="font-label-md text-label-md text-on-surface block">
                Allow remote LLM for Chat
              </span>
              <span className="text-on-surface-variant">
                Required with an API key before Chat can call a provider
                (<code className="font-technical-mono-sm text-technical-mono-sm text-primary">
                  allow_remote_llm
                </code>
                ).
              </span>
            </span>
          </label>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-md items-start">
            <div className="md:col-span-1 pt-sm">
              <label
                htmlFor="llm-base-url"
                className="font-label-md text-label-md text-foreground block"
              >
                Base URL
              </label>
            </div>
            <div className="md:col-span-3">
              <input
                id="llm-base-url"
                className="w-full bg-surface-container border border-border rounded-lg h-10 px-md font-technical-mono text-technical-mono text-foreground focus:outline-none focus:border-primary"
                type="url"
                value={llmBaseUrl}
                onChange={(e) => setLlmBaseUrl(e.target.value)}
                placeholder="https://api.openai.com/v1"
              />
              <p className="font-technical-mono-sm text-technical-mono-sm text-muted mt-xs">
                OpenAI-compatible{" "}
                <code className="text-primary">/chat/completions</code> endpoint.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-md items-start">
            <div className="md:col-span-1 pt-sm">
              <label
                htmlFor="llm-model"
                className="font-label-md text-label-md text-foreground block"
              >
                Model
              </label>
            </div>
            <div className="md:col-span-3">
              <input
                id="llm-model"
                className="w-full max-w-md bg-surface-container border border-border rounded-lg h-10 px-md font-technical-mono text-technical-mono text-foreground focus:outline-none focus:border-primary"
                type="text"
                value={llmModel}
                onChange={(e) => setLlmModel(e.target.value)}
                placeholder="gpt-4o-mini"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-md items-start">
            <div className="md:col-span-1 pt-sm">
              <label
                htmlFor="llm-api-key"
                className="font-label-md text-label-md text-foreground block"
              >
                API key
              </label>
            </div>
            <div className="md:col-span-3 space-y-sm">
              <input
                id="llm-api-key"
                className="w-full bg-surface-container border border-border rounded-lg h-10 px-md font-technical-mono text-technical-mono text-foreground focus:outline-none focus:border-primary"
                type="password"
                value={llmApiKey}
                onChange={(e) => setLlmApiKey(e.target.value)}
                placeholder={
                  llmKeyConfigured
                    ? "•••••••• (leave blank to keep)"
                    : "sk-… (optional if env is set)"
                }
                autoComplete="off"
              />
              <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
                Prefer env{" "}
                <code className="font-technical-mono-sm text-technical-mono-sm text-primary">
                  {llmKeyEnv}
                </code>
                . Otherwise Mycelium writes{" "}
                <code className="font-technical-mono-sm text-technical-mono-sm text-primary">
                  ~/.mycelium/llm_api_key
                </code>{" "}
                (mode 0600). Keys are never returned by the API or committed.
              </p>
              <p className="font-technical-mono-sm text-technical-mono-sm text-muted">
                Key status: {llmKeyConfigured ? "configured" : "not configured"}
              </p>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="button"
              disabled={savingLlm || !settings}
              onClick={() => void onSaveLlm()}
              className="px-xl h-10 rounded-xl bg-primary text-on-primary font-label-md text-label-md hover:brightness-110 transition-all duration-150 flex items-center gap-sm disabled:opacity-50"
            >
              <span className="material-symbols-outlined text-[18px]">save</span>
              {savingLlm ? "Saving…" : "Save Chat LLM"}
            </button>
          </div>
        </section>

        <section className="space-y-lg">
          <h3 className="font-label-caps text-label-caps text-on-surface-variant border-b border-border pb-xs uppercase tracking-widest">
            GitHub (optional)
          </h3>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Connect to import repos into Library for cross-repo search. Token is
            stored only under{" "}
            <code className="font-technical-mono-sm text-technical-mono-sm text-primary">
              ~/.mycelium/secrets/
            </code>
            .
          </p>
          <div className="p-md rounded-lg border border-border bg-surface-container-lowest flex flex-col gap-sm">
            <div className="flex items-center justify-between gap-md">
              <div>
                <p className="font-label-md text-label-md text-on-surface">
                  {github?.connected
                    ? `Connected as @${github.login}`
                    : "Not connected"}
                </p>
                <p className="font-technical-mono-sm text-technical-mono-sm text-muted">
                  {github?.connected
                    ? `mode=${github.auth_mode}`
                    : github?.oauth_configured
                      ? "OAuth device + PAT available"
                      : "PAT available · set client_id for device OAuth"}
                </p>
              </div>
              {github?.connected ? (
                <button
                  type="button"
                  onClick={() => void onDisconnect()}
                  className="px-md h-9 rounded-lg border border-border font-label-md text-label-md"
                >
                  Disconnect
                </button>
              ) : null}
            </div>

            {!github?.connected && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-md items-start pt-sm">
                  <div className="md:col-span-1">
                    <label className="font-label-md text-label-md text-foreground">
                      OAuth client_id
                    </label>
                  </div>
                  <div className="md:col-span-3 flex gap-sm">
                    <input
                      className="flex-1 bg-surface-container border border-border rounded-lg h-10 px-md font-technical-mono text-technical-mono text-foreground focus:outline-none focus:border-primary"
                      value={githubClientId}
                      onChange={(e) => setGithubClientId(e.target.value)}
                      placeholder="From GitHub → Settings → Developer settings"
                    />
                    <button
                      type="button"
                      disabled={polling || !githubClientId.trim()}
                      onClick={() => void onDeviceStart()}
                      className="px-md h-10 rounded-xl bg-primary text-on-primary font-label-md text-label-md disabled:opacity-50"
                    >
                      {polling ? "Waiting…" : "Device login"}
                    </button>
                  </div>
                </div>
                {deviceCode && (
                  <p className="font-body-sm text-body-sm text-on-surface">
                    Open{" "}
                    <a
                      className="text-primary underline"
                      href={deviceUri ?? "https://github.com/login/device"}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {deviceUri}
                    </a>{" "}
                    and enter code{" "}
                    <code className="font-technical-mono text-technical-mono text-primary">
                      {deviceCode}
                    </code>
                  </p>
                )}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-md items-start">
                  <div className="md:col-span-1">
                    <label className="font-label-md text-label-md text-foreground">
                      Or paste PAT
                    </label>
                  </div>
                  <div className="md:col-span-3 flex gap-sm">
                    <input
                      className="flex-1 bg-surface-container border border-border rounded-lg h-10 px-md font-technical-mono text-technical-mono text-foreground focus:outline-none focus:border-primary"
                      type="password"
                      value={pat}
                      onChange={(e) => setPat(e.target.value)}
                      placeholder="ghp_… or github_pat_…"
                    />
                    <button
                      type="button"
                      disabled={!pat.trim()}
                      onClick={() => void onSavePat()}
                      className="px-md h-10 rounded-xl border border-border font-label-md text-label-md disabled:opacity-50"
                    >
                      Save token
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </section>

        <section className="space-y-lg">
          <h3 className="font-label-caps text-label-caps text-on-surface-variant border-b border-border pb-xs uppercase tracking-widest">
            Paths &amp; Storage
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-md items-start">
            <div className="md:col-span-1 pt-sm">
              <label className="font-label-md text-label-md text-foreground block">
                Vault path
              </label>
            </div>
            <div className="md:col-span-3">
              <input
                className="w-full bg-surface-container border border-border rounded-lg h-10 px-md font-technical-mono text-technical-mono text-primary focus:outline-none focus:border-primary transition-colors duration-150"
                type="text"
                value={vaultDir}
                onChange={(e) => setVaultDir(e.target.value)}
              />
            </div>
          </div>
        </section>

        <section className="space-y-lg">
          <h3 className="font-label-caps text-label-caps text-on-surface-variant border-b border-border pb-xs uppercase tracking-widest">
            Local Indexing
          </h3>

          <div className="space-y-sm">
            <div className="flex flex-wrap items-baseline justify-between gap-sm">
              <label className="font-label-md text-label-md text-foreground">
                Embedding model
              </label>
              <p className="font-technical-mono-sm text-technical-mono-sm text-muted">
                Active: {runtime.model_id ?? settings?.embedding_model ?? "…"} ·{" "}
                {runtime.backend ?? "…"}
              </p>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Changing model updates config; restart Core, then re-index workspaces
              so vectors match.
            </p>
            {runtime.backend === "hashing" &&
              (runtime.notice || "")
                .toLowerCase()
                .includes("falling back") && (
              <p className="font-body-sm text-body-sm text-on-surface-variant rounded-lg border border-border bg-surface-container-lowest px-md py-sm">
                Packaged Desktop is currently on the offline hashing embedder
                (sentence-transformers is not bundled yet). Indexing still
                completes; semantic search quality is limited.
              </p>
            )}
            <div className="grid gap-sm" role="radiogroup" aria-label="Embedding model">
              {MODEL_OPTIONS.map((opt) => {
                const selected = model === opt.id;
                return (
                  <button
                    key={opt.id}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    onClick={() => setModel(opt.id)}
                    className={`text-left rounded-xl border px-md py-md transition-colors duration-150 ${
                      selected
                        ? "border-primary/50 bg-accent-dim shadow-[inset_0_0_0_1px_rgba(0,209,178,0.22)]"
                        : "border-border bg-surface-container-lowest hover:border-primary/30 hover:bg-surface-container-high/40"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-md">
                      <div className="min-w-0 space-y-xs">
                        <div className="flex flex-wrap items-center gap-sm">
                          <span className="font-label-md text-label-md text-on-surface">
                            {opt.name}
                          </span>
                          <span
                            className={`rounded-md px-sm py-px font-label-caps text-label-caps uppercase tracking-wider ${
                              opt.badge === "Recommended"
                                ? "bg-primary/15 text-primary"
                                : opt.badge === "Tests only"
                                  ? "bg-surface-container-high text-muted"
                                  : "bg-surface-container-high text-on-surface-variant"
                            }`}
                          >
                            {opt.badge}
                          </span>
                        </div>
                        <p className="font-body-sm text-body-sm text-on-surface-variant">
                          {opt.blurb}
                        </p>
                        <p className="font-technical-mono-sm text-technical-mono-sm text-muted truncate">
                          {opt.detail}
                        </p>
                      </div>
                      <span
                        className={`mt-xs flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${
                          selected
                            ? "border-primary bg-primary text-on-primary"
                            : "border-border bg-transparent"
                        }`}
                        aria-hidden
                      >
                        {selected ? (
                          <span className="material-symbols-outlined text-[14px]">
                            check
                          </span>
                        ) : null}
                      </span>
                    </div>
                  </button>
                );
              })}
              {!MODEL_OPTIONS.some((o) => o.id === model) && model ? (
                <button
                  type="button"
                  role="radio"
                  aria-checked
                  className="text-left rounded-xl border border-primary/50 bg-accent-dim px-md py-md"
                >
                  <p className="font-label-md text-label-md text-on-surface">
                    Custom model
                  </p>
                  <p className="font-technical-mono-sm text-technical-mono-sm text-muted mt-xs break-all">
                    {model}
                  </p>
                </button>
              ) : null}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-md items-start pt-md">
            <div className="md:col-span-1 pt-sm">
              <label className="font-label-md text-label-md text-foreground block">
                Git history depth
              </label>
            </div>
            <div className="md:col-span-3">
              <input
                className="w-24 bg-surface-container border border-border rounded-lg h-10 px-sm font-technical-mono text-technical-mono text-foreground text-center focus:outline-none focus:border-primary transition-colors duration-150"
                type="number"
                min={1}
                value={historyDepth}
                onChange={(e) => setHistoryDepth(Number(e.target.value) || 1)}
              />
            </div>
          </div>
          <div className="flex justify-end pt-lg">
            <button
              type="button"
              disabled={saving || !settings}
              onClick={() => void onApply()}
              className="px-xl h-10 rounded-xl bg-primary text-on-primary font-label-md text-label-md hover:brightness-110 transition-all duration-150 flex items-center gap-sm disabled:opacity-50"
            >
              <span className="material-symbols-outlined text-[18px]">save</span>
              {saving ? "Saving…" : "Apply Changes"}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
