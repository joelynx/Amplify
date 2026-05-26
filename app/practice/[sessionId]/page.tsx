import { PracticeRunner } from "./runner";

type Props = { params: Promise<{ sessionId: string }> };

export default async function PracticeSessionPage({ params }: Props) {
  const { sessionId } = await params;
  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <PracticeRunner sessionId={sessionId} />
    </main>
  );
}
