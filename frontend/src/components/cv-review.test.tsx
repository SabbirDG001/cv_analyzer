import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("@/lib/api", () => ({ apiFetch: (...args: unknown[]) => apiFetch(...args) }));

import { CvReviewForm, addMatch } from "./cv-review";
import type { CvReview } from "@/lib/types";

const review: CvReview = {
  cv_id: "c1",
  parsed: {
    cgpa: 3.6,
    projects: [{ title: "RNA-seq analysis", summary: "" }],
    experience: [],
    languages: ["Bangla"],
    test_scores: [],
    interests: [],
  },
  matched: [{ skill_id: 1, name: "Python", level: 3, evidence: "RNA-seq plots" }],
  unmatched: [{ name: "Basket Weaving", level: 1, evidence: "hobby" }],
};

afterEach(() => apiFetch.mockReset());

describe("addMatch", () => {
  it("keeps the higher level when a skill is already present", () => {
    const list = [{ skill_id: 1, name: "Python", level: 3, evidence: "" }];
    expect(addMatch(list, { ...list[0], level: 2 })[0].level).toBe(3);
    expect(addMatch(list, { ...list[0], level: 5 })[0].level).toBe(5);
    expect(addMatch(list, { skill_id: 2, name: "R", level: 1, evidence: "" })).toHaveLength(2);
  });
});

describe("CvReviewForm", () => {
  it("confirms edited levels and removed skills", () => {
    apiFetch.mockResolvedValue([]);
    const onConfirm = vi.fn();
    render(<CvReviewForm review={review} busy={false} onConfirm={onConfirm} />);
    fireEvent.click(screen.getByRole("button", { name: "5 - Expert" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm and save skills" }));
    expect(onConfirm).toHaveBeenCalledWith([{ skill_id: 1, level: 5 }]);
  });

  it("disables confirm when nothing is left", () => {
    apiFetch.mockResolvedValue([]);
    render(<CvReviewForm review={review} busy={false} onConfirm={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Remove" }));
    expect(screen.getByRole("button", { name: "Confirm and save skills" })).toBeDisabled();
  });

  it("maps an unmatched skill to a real one using the suggested level", async () => {
    apiFetch.mockResolvedValue([{ id: 9, name: "Handicrafts", category: "x", aliases: [] }]);
    const onConfirm = vi.fn();
    render(<CvReviewForm review={review} busy={false} onConfirm={onConfirm} />);
    fireEvent.click(await screen.findByRole("button", { name: "Handicrafts" }));
    await waitFor(() => expect(screen.queryByText("Skills we could not match")).toBeNull());
    fireEvent.click(screen.getByRole("button", { name: "Confirm and save skills" }));
    expect(onConfirm).toHaveBeenCalledWith([
      { skill_id: 1, level: 3 },
      { skill_id: 9, level: 1 },
    ]);
  });

  it("shows extra CV facts that are not skills", () => {
    apiFetch.mockResolvedValue([]);
    render(<CvReviewForm review={review} busy={false} onConfirm={vi.fn()} />);
    expect(screen.getByText("RNA-seq analysis")).toBeInTheDocument();
    expect(screen.getByText("Bangla")).toBeInTheDocument();
  });
});
