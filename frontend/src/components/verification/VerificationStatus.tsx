import type { Claim } from "../../types/research";
import { Badge } from "../ui/Badge";
import { mapVerificationStatus } from "../../utils/verificationStatus";

interface VerificationStatusProps {
  status: Claim["status"];
}

export function VerificationStatus({ status }: VerificationStatusProps) {
  const mapped = mapVerificationStatus(status);
  return <Badge variant={mapped.variant}>{mapped.label}</Badge>;
}
