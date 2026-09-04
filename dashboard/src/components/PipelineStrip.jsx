/**
 * Pipeline status strip - dashboard.md §2. 4-step live trace: report
 * detected -> history read -> sector ranked -> verdict generated.
 * Backed by GET /api/pipeline-status/{ticker} (kuartal/api/mock_data.py
 * mock_pipeline_status), NOT part of the §3 company contract - poll it
 * separately. This is the one place motion is allowed (dashboard.md §5).
 * TODO(dashboard owner): poll on an interval while a run is in flight,
 * real reveal animation, reuse for both the simulate button and real runs.
 *
 * @param {string} ticker
 */
import { useEffect, useState } from "react";
import { getPipelineStatus } from "../api/client.js";

export default function PipelineStrip({ ticker }) {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getPipelineStatus(ticker)
      .then((res) => !cancelled && setStatus(res))
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  if (!status) return null;

  return (
    <ol className="kt-hairline kt-mono" style={{ display: "flex", gap: "1rem", listStyle: "none" }}>
      {status.steps.map((step) => (
        <li key={step.name} style={{ opacity: step.status === "pending" ? 0.4 : 1 }}>
          {step.name}
        </li>
      ))}
    </ol>
  );
}
