import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Flame, EyeOff } from 'lucide-react';

const HeatmapOverlay = ({ documentId, documentText, enabled }) => {
  const [heatmap, setHeatmap] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!enabled || !documentId) return;

    const fetchHeatmap = async () => {
      setIsLoading(true);
      try {
        const response = await axios.get(`/api/documents/${documentId}/heatmap`);
        setHeatmap(response.data);
      } catch (err) {
        console.error('Failed to load heatmap', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchHeatmap();
  }, [documentId, enabled]);

  const paragraphs = useMemo(() => {
    if (!documentText) return [];
    return documentText.split(/\n\s*\n/).map((value) => value.trim()).filter(Boolean);
  }, [documentText]);

  const hasRealHeatmapData = (heatmap?.paragraphs || []).some((item) => item.score_percent > 0);

  if (!enabled) {
    return null;
  }

  if (isLoading) {
    return <div className="text-sm text-[#b89c86]">Loading confusion insights…</div>;
  }

  const paragraphData = heatmap?.paragraphs || [];

  return (
    <div className="space-y-3">
      <div className="rounded-xl border border-[#5f4635] bg-[#2b221d] p-3 text-sm text-[#f4e5d6]">
        <div className="mb-2 flex items-center gap-2 text-[#f7cc9d]">
          <Flame className="h-4 w-4" />
          Confusion heatmap
        </div>
        {hasRealHeatmapData ? (
          <div className="text-xs text-[#d8c0a6]">
            Sections that drew the most doubt questions are highlighted more strongly.
          </div>
        ) : (
          <div className="text-xs text-[#d8c0a6]">
            No doubt-question data has been collected yet. Ask questions in the tutor chat to start building the heatmap.
          </div>
        )}
      </div>

      <div className="space-y-3 text-sm leading-relaxed text-[#6a5347]">
        {paragraphs.map((paragraph, index) => {
          const paragraphScore = paragraphData[index]?.score_percent || 0;
          const opacity = paragraphScore > 0
            ? Math.min(0.28, 0.08 + paragraphScore / 200)
            : (hasRealHeatmapData ? 0.02 : 0.04);
          const backgroundColor = `rgba(246, 179, 45, ${opacity})`;
          return (
            <div
              key={`${paragraph.slice(0, 20)}-${index}`}
              className="rounded-xl border border-[#5f4635]/30 p-3 transition-all"
              style={{ backgroundColor }}
              title={paragraphScore > 0 ? `About ${paragraphScore}% of learners asked about this section.` : 'No doubt data yet — ask a question to build the heatmap.'}
            >
              <div className="whitespace-pre-wrap font-mono">{paragraph}</div>
              <div className="mt-2 text-[11px] text-[#8c6b5d]">
                {paragraphScore > 0 ? `${paragraphScore}% of students asked about this section` : 'No doubt data yet'}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default HeatmapOverlay;
