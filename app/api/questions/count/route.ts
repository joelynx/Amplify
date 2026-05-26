import { NextResponse, type NextRequest } from "next/server";
import { getServerSupabase } from "@/lib/supabase/server";
import { countMatchingQuestions } from "@/lib/queries";
import type { PracticeFilters } from "@/lib/db/types";

export async function POST(request: NextRequest) {
  const body = (await request.json()) as { filters?: PracticeFilters };
  const filters = body.filters ?? {};

  const supabase = await getServerSupabase();
  try {
    const count = await countMatchingQuestions(supabase, filters);
    return NextResponse.json({ count });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 500 }
    );
  }
}
