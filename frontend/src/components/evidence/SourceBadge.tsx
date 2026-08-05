import { Badge } from "../ui/Badge";
import type { Source } from "../../types/research";

interface SourceBadgeProps {
  tier: Source["tier"];
}

export function SourceBadge({ tier }: SourceBadgeProps) {
  switch (tier) {
    case "HIGH":
      return <Badge variant="success">Trusted Source</Badge>;
    case "MEDIUM":
      return <Badge variant="warning">Moderate Source</Badge>;
    case "LOW":
      return <Badge variant="error">Limited Source</Badge>;
    default:
      return <Badge variant="neutral">Unknown Source</Badge>;
  }
}
