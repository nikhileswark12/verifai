import type { Claim } from "../types/research";

export type MappedVerificationStatus = 
  | { variant: "success"; label: "✓ Supported" }
  | { variant: "warning"; label: "⚠ Limited Evidence" }
  | { variant: "error"; label: "! Conflicting Sources" }
  | { variant: "neutral"; label: "? Not Supported" };

export function mapVerificationStatus(status: Claim["status"]): MappedVerificationStatus {
  switch (status) {
    case "VERIFIED":
      return { variant: "success", label: "✓ Supported" };
    case "WEAKLY_SUPPORTED":
      return { variant: "warning", label: "⚠ Limited Evidence" };
    case "CONFLICTING":
      return { variant: "error", label: "! Conflicting Sources" };
    case "UNSUPPORTED":
    default:
      return { variant: "neutral", label: "? Not Supported" };
  }
}
