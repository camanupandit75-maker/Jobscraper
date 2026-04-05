import { formatDistanceToNow } from "date-fns";

type Props = {
  endedAt: string | null | undefined;
  status?: string;
};

export function ScrapeStatusBadge({ endedAt, status }: Props) {
  if (!endedAt) {
    return (
      <span className="text-[var(--muted)] text-xs font-mono tracking-wide">
        Last scrape: —
      </span>
    );
  }
  try {
    const rel = formatDistanceToNow(new Date(endedAt), { addSuffix: true });
    const ok = status !== "error";
    return (
      <span
        className={`text-xs font-mono tracking-wide ${
          ok ? "text-[var(--success)]" : "text-[var(--danger)]"
        }`}
      >
        Last scrape: {rel}
      </span>
    );
  } catch {
    return (
      <span className="text-[var(--muted)] text-xs font-mono">Last scrape: —</span>
    );
  }
}
