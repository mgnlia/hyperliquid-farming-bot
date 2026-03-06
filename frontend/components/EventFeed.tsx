interface Props {
  events: Array<Record<string, unknown>>;
}

export function EventFeed({ events }: Props) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-200">Live SSE Event Feed</h3>
      <div className="max-h-80 space-y-2 overflow-auto">
        {events.length === 0 ? (
          <p className="text-sm text-slate-500">No stream events yet.</p>
        ) : (
          events
            .slice()
            .reverse()
            .map((event, index) => (
              <pre
                key={`${String(event.type ?? "event")}-${index}`}
                className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900/60 p-2 text-xs text-slate-300"
              >
                {JSON.stringify(event, null, 2)}
              </pre>
            ))
        )}
      </div>
    </section>
  );
}
