import { describe, expect, it } from "vitest";

import { toProfileInput, validateProfile, type ProfileForm } from "./validation";

const valid: ProfileForm = {
  name: " Rina Akter ",
  university: "University of Dhaka",
  year: "3",
  department: "Biochemistry",
  cgpa: "3.5",
  fieldId: "1",
  track: "research",
};

describe("validateProfile", () => {
  it("accepts a complete profile", () => {
    expect(validateProfile(valid)).toEqual({});
  });

  it("flags missing required text fields", () => {
    const errors = validateProfile({ ...valid, name: "  ", fieldId: "", track: "" });
    expect(Object.keys(errors).sort()).toEqual(["fieldId", "name", "track"]);
  });

  it.each(["0", "9", "2.5", "abc", ""])("rejects year %s", (year) => {
    expect(validateProfile({ ...valid, year }).year).toBeDefined();
  });

  it.each(["4.01", "-0.1", "abc", ""])("rejects cgpa %s", (cgpa) => {
    expect(validateProfile({ ...valid, cgpa }).cgpa).toBeDefined();
  });

  it.each(["0", "4", "3.99"])("accepts cgpa %s", (cgpa) => {
    expect(validateProfile({ ...valid, cgpa }).cgpa).toBeUndefined();
  });

  it("rejects an unknown track", () => {
    expect(validateProfile({ ...valid, track: "gap-year" }).track).toBeDefined();
  });
});

describe("toProfileInput", () => {
  it("trims text and formats numbers for the API", () => {
    expect(toProfileInput(valid)).toEqual({
      name: "Rina Akter",
      university: "University of Dhaka",
      year: 3,
      department: "Biochemistry",
      cgpa: "3.50",
      track: "research",
      field_id: 1,
    });
  });
});
