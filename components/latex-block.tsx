import { renderLatex } from "@/lib/katex";

// Render LaTeX to a React element (server-safe).
export function LatexBlock({
  src,
  className,
}: {
  src: string;
  className?: string;
}) {
  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: renderLatex(src) }}
    />
  );
}
