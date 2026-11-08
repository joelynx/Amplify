import { describe, expect, it } from "vitest";

import { leafKey, templateToLeaves } from "../generate";
import { SELF_EXPLAIN_PROMPTS, promptFor } from "../../components/notes/QuestionNotes";

const tree = {
  Calculus: { Integral: ["Riemann", "Techniques"], Differential: ["Limits"] },
  "Linear Algebra": { Eigen: ["Diagonal"] },
};

describe("templateToLeaves", () => {
  it("uses subtopics when the template names them", () => {
    const got = templateToLeaves({ subtopic_list: ["Limits"], topic_list: ["Linear Algebra"] }, tree);
    expect([...got]).toEqual([leafKey("Calculus", "Differential", "Limits")]);
  });

  it("expands branches, then topics (Trends and Practise this send topics)", () => {
    expect(templateToLeaves({ subtopic_list: [], branch_list: ["Integral"] }, tree).size).toBe(2);
    const got = templateToLeaves({ subtopic_list: [], branch_list: [], topic_list: ["Linear Algebra"] }, tree);
    expect([...got]).toEqual([leafKey("Linear Algebra", "Eigen", "Diagonal")]);
  });

  it("is empty for an empty template", () => {
    expect(templateToLeaves({ subtopic_list: [] }, tree).size).toBe(0);
  });
});

describe("self-explanation prompts", () => {
  it("picks the same prompt for a question every time", () => {
    expect(promptFor(12)).toBe(promptFor(12));
    expect(SELF_EXPLAIN_PROMPTS).toContain(promptFor(7));
  });
});
