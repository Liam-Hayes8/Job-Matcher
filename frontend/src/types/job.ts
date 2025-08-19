export type Job = {
  id?: string | number;
  title: string;
  company: string;
  location?: string;
  description?: string;
  apply_url: string;
  source?: string;
};

export type JobMatch = Job & {
  match_score?: number;
  matching_skills?: string[];
};


