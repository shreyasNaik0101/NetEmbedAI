import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import ShowcaseNotice from "./ShowcaseNotice";

it("makes the limits of model labels and scores visible", () => {
  render(<ShowcaseNotice />);
  const note = screen.getByLabelText("Prototype limitations");
  expect(note).toHaveTextContent(
    "Model scores are not probabilities of correctness",
  );
  expect(note).toHaveTextContent("local reliability varies");
});
