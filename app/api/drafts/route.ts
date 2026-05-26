import { NextResponse, type NextRequest } from "next/server";
import crypto from "node:crypto";
import { GoogleGenerativeAI } from "@google/generative-ai";
import { getServerSupabase } from "@/lib/supabase/server";
import { getAdminSupabase } from "@/lib/supabase/admin";
import { rateLimit, clientKey } from "@/lib/rate-limit";

const EMBED_MODEL = "gemini-embedding-001";
const MAX_LATEX_BYTES = 16_000;
const MAX_SOLUTION_BYTES = 16_000;

function normalize(s: string): string {
  return s.replace(/\s+/g, " ").trim();
}

function slugify(s: string): string {
  return s
    .toLowerCase()
    .replace(/['']/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const supabase = await getServerSupabase();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  // Rate limit BEFORE doing any DB / embedding work — caps a hostile TA at
  // 10 submissions per minute, plenty for any real authoring session.
  const rl = rateLimit(clientKey(request, user.id) + ":drafts", 10, 60_000);
  if (!rl.allowed) {
    return NextResponse.json(
      { error: "rate limited — try again shortly" },
      { status: 429, headers: { "Retry-After": String(Math.ceil(rl.retryAfterMs / 1000)) } }
    );
  }

  const { data: profile } = await supabase
    .from("user_profiles")
    .select("role, institution_id")
    .eq("user_id", user.id)
    .maybeSingle();

  const role = (profile as { role?: string } | null)?.role;
  if (role !== "faculty" && role !== "admin" && role !== "moderator") {
    return NextResponse.json(
      { error: "Authoring is gated to TAs / faculty / admins." },
      { status: 403 }
    );
  }

  if (!body.latexcode || !body.topic || !body.branch || !body.subtopic) {
    return NextResponse.json(
      { error: "Missing required fields (topic, branch, subtopic, latexcode)." },
      { status: 400 }
    );
  }

  // Content-length guards — reject pathological payloads that would blow up
  // KaTeX render or Gemini embedding cost.
  if (typeof body.latexcode !== "string" || body.latexcode.length > MAX_LATEX_BYTES) {
    return NextResponse.json(
      { error: `Question body exceeds ${MAX_LATEX_BYTES} chars.` },
      { status: 413 }
    );
  }
  if (
    body.solution &&
    (typeof body.solution !== "string" || body.solution.length > MAX_SOLUTION_BYTES)
  ) {
    return NextResponse.json(
      { error: `Solution exceeds ${MAX_SOLUTION_BYTES} chars.` },
      { status: 413 }
    );
  }
  for (const f of ["topic", "branch", "subtopic", "source", "answer"]) {
    const v = body[f];
    if (v && (typeof v !== "string" || v.length > 200)) {
      return NextResponse.json(
        { error: `Field "${f}" exceeds 200 chars.` },
        { status: 413 }
      );
    }
  }

  // Use the admin client for the live-insert path so RLS doesn't block.
  const admin = getAdminSupabase();
  const latex_hash = crypto
    .createHash("sha256")
    .update(normalize(body.latexcode))
    .digest("hex");

  // Reject duplicates by content hash.
  const { data: existing } = await admin
    .from("questions")
    .select("id")
    .eq("latex_hash", latex_hash)
    .maybeSingle();
  if (existing) {
    return NextResponse.json(
      { error: "This exact question is already in the bank.", id: existing.id },
      { status: 409 }
    );
  }

  const insert = await admin
    .from("questions")
    .insert({
      topic: body.topic,
      branch: body.branch,
      subtopic: body.subtopic,
      type: body.type ?? "explanation/reasoning",
      in_syllabus: true,
      source: body.source || `user:${user.email}`,
      submitted_by: user.email,
      answer: body.answer ?? null,
      solution: body.solution ?? null,
      latexcode: body.latexcode,
      latex_hash,
    })
    .select("id")
    .single();

  if (insert.error) {
    return NextResponse.json({ error: insert.error.message }, { status: 500 });
  }
  const questionId = insert.data.id as number;

  // Tags — synthesize from subtopic chunks + type + source (best-effort).
  const tagSet = new Set<string>();
  for (const chunk of (body.subtopic as string).split("/")) {
    const slug = slugify(chunk.trim());
    if (slug) tagSet.add(slug);
  }
  if (body.type) tagSet.add(slugify(body.type));
  if (body.source) tagSet.add(slugify(body.source));
  if (tagSet.size > 0) {
    await admin
      .from("question_tags")
      .upsert(
        [...tagSet].map((tag) => ({ question_id: questionId, tag })),
        { onConflict: "question_id,tag", ignoreDuplicates: true }
      );
  }

  // Embedding — generate via Gemini, store in question_embeddings.
  // Best-effort: a failure here doesn't roll back the question insert.
  try {
    const apiKey = process.env.GOOGLE_API_KEY;
    if (apiKey) {
      const genAI = new GoogleGenerativeAI(apiKey);
      const model = genAI.getGenerativeModel({ model: EMBED_MODEL });
      const res = await model.embedContent({
        content: { role: "user", parts: [{ text: body.latexcode }] },
        taskType: "SEMANTIC_SIMILARITY" as never,
        outputDimensionality: 768,
      } as never);
      const vec = res.embedding.values as number[];
      const vecLiteral = `[${vec.join(",")}]`;
      await admin.from("question_embeddings").insert({
        question_id: questionId,
        model: EMBED_MODEL,
        embedding: vecLiteral,
      });
    }
  } catch (err) {
    console.error("Embedding generation failed (question kept):", err);
  }

  return NextResponse.json({
    id: questionId,
    message: "live",
  });
}
