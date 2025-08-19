import type { Job } from "../types/job";

export function normalizeJob(raw: any): Job {
  const apply_url =
    raw?.apply_url ??
    raw?.applyUrl ??
    raw?.url ??
    raw?.job_url ??
    raw?.jobUrl ??
    "";

  return {
    id: raw?.id ?? raw?.job_id ?? undefined,
    title: raw?.title ?? "",
    company: raw?.company ?? raw?.organization ?? "",
    location: raw?.location ?? raw?.locations ?? "",
    description: raw?.description ?? "",
    job_type: raw?.job_type ?? raw?.type ?? undefined,
    salary_min: raw?.salary_min ?? undefined,
    salary_max: raw?.salary_max ?? undefined,
    remote: raw?.remote ?? undefined,
    apply_url,
    source: raw?.source ?? raw?.ats ?? undefined,
  };
}

export async function fetchLiveJobs(opts: {
  resumeId?: string;               // preferred
  resumeText?: string;             // fallback if no id yet
  location?: string;
  limit?: number;
  debug?: boolean;
}): Promise<{ jobs: Job[]; debug: any }> {
  const body: any = {
    location: opts.location ?? "US",
    limit: opts.limit ?? 40,
    debug: !!opts.debug,
    ...(opts.resumeId ? { resume_id: opts.resumeId } : { resume_text: opts.resumeText ?? "" }),
  };

  const res = await fetch("/api/v1/jobs/live", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText));
  const data = await res.json().catch(() => ({}));
  const rawList = Array.isArray(data.jobs) ? data.jobs : [];
  const jobs: Job[] = rawList
    .map(normalizeJob)
    .filter((j: Job) => typeof j.apply_url === "string" && j.apply_url.length > 0);
  return { jobs, debug: data.debug ?? null };
}
