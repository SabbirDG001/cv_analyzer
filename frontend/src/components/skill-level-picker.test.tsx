import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SkillLevelPicker } from "./skill-level-picker";

describe("SkillLevelPicker", () => {
  it("offers levels 0 to 5", () => {
    render(<SkillLevelPicker value={null} onChange={() => {}} />);
    expect(screen.getAllByRole("button").map((b) => b.textContent)).toEqual([
      "0",
      "1",
      "2",
      "3",
      "4",
      "5",
    ]);
  });

  it("marks only the current level as pressed", () => {
    render(<SkillLevelPicker value={3} onChange={() => {}} />);
    const pressed = screen.getAllByRole("button", { pressed: true });
    expect(pressed).toHaveLength(1);
    expect(pressed[0]).toHaveTextContent("3");
  });

  it("reports the chosen level", async () => {
    const onChange = vi.fn();
    render(<SkillLevelPicker value={1} onChange={onChange} />);
    await userEvent.click(screen.getByRole("button", { name: /Strong/ }));
    expect(onChange).toHaveBeenCalledWith(4);
  });

  it("does nothing when disabled", async () => {
    const onChange = vi.fn();
    render(<SkillLevelPicker value={1} onChange={onChange} disabled />);
    await userEvent.click(screen.getByRole("button", { name: /Strong/ }));
    expect(onChange).not.toHaveBeenCalled();
  });
});
