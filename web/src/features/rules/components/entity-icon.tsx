// Glyph hover colors rely on an ancestor carrying the row's `group` class.

export function FolderGlyph() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="size-6 shrink-0 text-stone-400 transition-colors duration-200 group-hover:text-stone-600"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
    </svg>
  );
}

interface FileGlyphProps {
  extension?: string;
}

export function FileGlyph({ extension }: FileGlyphProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      className="size-6 shrink-0 text-stone-400 transition-colors duration-200 group-hover:text-stone-600"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M5.5 2h8.25L20.5 8.75V20c0 1.1-.9 2-2 2h-13c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2Z" />
      <path d="M13.75 2 20.5 8.75h-5.25c-.83 0-1.5-.67-1.5-1.5V2Z" />
      {extension ? (
        <text
          x="12"
          y="17.5"
          textAnchor="middle"
          stroke="none"
          className="fill-stone-600 font-mono text-[6px] font-semibold tracking-tight uppercase transition-colors duration-200 group-hover:fill-stone-800"
        >
          {extension}
        </text>
      ) : null}
    </svg>
  );
}
