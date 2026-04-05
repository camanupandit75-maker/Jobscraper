export type JobStatus = "new" | "bookmarked" | "applied" | "hidden";
export type JobSource = "remoteok" | "indeed" | "naukri" | "linkedin" |
                        "wellfound" | "internshala" | "glassdoor";

export interface Job {
  id: string;
  hash: string;
  title: string;
  company: string;
  location: string;
  job_type: string;
  salary: string;
  url: string;
  description: string;
  source: JobSource | string;
  posted_at: string;
  scraped_at: string;
  status: JobStatus | string;
  is_bookmarked: boolean;
  is_hidden: boolean;
  applied_at: string | null;
}

export interface ScrapeRun {
  id: string;
  started_at: string;
  ended_at: string | null;
  jobs_added: number;
  jobs_found: number;
  source: string;
  status: string;
}

export interface JobFilters {
  search: string;
  source: string;
  status: string;
  job_type: string;
  location: string;
}
