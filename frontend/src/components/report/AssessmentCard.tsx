import { Card, CardContent } from "../ui/Card";

interface AssessmentCardProps {
  assessment?: string;
}

export function AssessmentCard({ assessment }: AssessmentCardProps) {
  if (!assessment) return null;

  return (
    <Card>
      <CardContent className="p-6 space-y-4 bg-blue-50/50">
        <h3 className="text-lg font-semibold text-slate-900">
          Overall Assessment
        </h3>
        <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
          {assessment}
        </p>
      </CardContent>
    </Card>
  );
}
