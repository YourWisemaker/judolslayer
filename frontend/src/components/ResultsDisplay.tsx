import { SpamResults } from './SpamResults';
import { SpamDetectionResponse } from '@/lib/api';

interface ResultsDisplayProps {
  data: SpamDetectionResponse;
  isDryRun: boolean;
}

export function ResultsDisplay({ data, isDryRun }: ResultsDisplayProps) {
  return (
    <div className="mt-8">
      <SpamResults data={data} isDryRun={isDryRun} />
    </div>
  );
}