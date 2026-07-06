import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useI18n } from "../lib/i18n";
import { api, DebateTranscript, Project } from "../lib/api";
import { DebateColumn } from "../components/DebateColumn";
import { VerdictBanner } from "../components/VerdictBanner";
import { SkeletonLoader } from "../components/SkeletonLoader";

export function DebatePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { t } = useI18n();
  const [project, setProject] = useState<Project | null>(null);
  const [transcript, setTranscript] = useState<DebateTranscript | null>(null);
  const [step, setStep] = useState(0); // step-through reveal, 0 = nothing shown yet
  const [liveLoading, setLiveLoading] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    api.getProject(projectId).then((d) => setProject(d.project));
    api.getDebate(projectId).then(setTranscript);
    setStep(3); // default: show everything (step-through is an optional demo affordance)
  }, [projectId]);

  const runLive = async () => {
    if (!projectId) return;
    setLiveLoading(true);
    setStep(0);
    try {
      const fresh = await api.runLiveDebate(projectId);
      setTranscript(fresh);
      setStep(3);
    } finally {
      setLiveLoading(false);
    }
  };

  if (!transcript || !project) {
    return (
      <div className="space-y-4">
        <SkeletonLoader className="h-8 w-1/2" />
        <div className="grid grid-cols-2 gap-4">
          <SkeletonLoader className="h-64" />
          <SkeletonLoader className="h-64" />
        </div>
      </div>
    );
  }

  const red = transcript.turns.find((t) => t.agent === "red");
  const blue = transcript.turns.find((t) => t.agent === "blue");
  const council = transcript.turns.find((t) => t.agent === "council");

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs text-ink-400">
          <Link to={`/project/${projectId}`} className="hover:underline">
            {project.name}
          </Link>
        </p>
        <h1 className="text-2xl font-bold text-ink-900 mt-1">{t("debate.title")}</h1>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        {red && step >= 1 && <DebateColumn side="red" arguments={red.arguments} />}
        {blue && step >= 2 && <DebateColumn side="blue" arguments={blue.arguments} />}
      </div>

      {council && step >= 3 && council.score !== null && council.rationale && (
        <VerdictBanner score={council.score} rationale={council.rationale} />
      )}

      <div className="flex items-center justify-between text-xs text-ink-400">
        <span>{t("debate.poweredBy")}</span>
        <button
          onClick={runLive}
          disabled={liveLoading}
          className="px-4 py-2 rounded-btn border border-bl-border text-ink-600 font-medium hover:border-teal-500 hover:text-teal-500 disabled:opacity-50"
        >
          {liveLoading ? "Running…" : t("debate.watchLive")}
        </button>
      </div>
    </div>
  );
}
