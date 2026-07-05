import { useMemo, useState } from 'react';
import axios from 'axios';

const FeedbackWidget = ({ featureType, referenceId }) => {
  const [showCommentBox, setShowCommentBox] = useState(false);
  const [comment, setComment] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const sessionId = useMemo(() => {
    if (typeof window === 'undefined') return 'anonymous';
    let existing = window.localStorage.getItem('sitecraft_session_id');
    if (!existing) {
      existing = `session-${Math.random().toString(36).slice(2, 10)}`;
      window.localStorage.setItem('sitecraft_session_id', existing);
    }
    return existing;
  }, []);

  const submitFeedback = async (rating) => {
    if (submitted) return;
    setSubmitted(true);
    try {
      await axios.post('/api/feedback', {
        session_id: sessionId,
        feature_type: featureType,
        reference_id: referenceId || null,
        rating,
        comment: comment.trim() || null,
      });
    } catch (err) {
      console.error('Feedback submission failed', err);
    }
  };

  const handleCommentSubmit = async (event) => {
    event.preventDefault();
    await submitFeedback(1);
  };

  return (
    <div className="mt-3 flex flex-col items-start gap-2 text-xs text-[#b89c86]">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => submitFeedback(1)}
          className="rounded-full border border-[#5f4635] px-2 py-1 hover:bg-[#3d2d22]"
        >
          👍 Helpful
        </button>
        <button
          type="button"
          onClick={() => submitFeedback(-1)}
          className="rounded-full border border-[#5f4635] px-2 py-1 hover:bg-[#3d2d22]"
        >
          👎 Needs work
        </button>
        <button
          type="button"
          onClick={() => setShowCommentBox((prev) => !prev)}
          className="text-[#f7cc9d]"
        >
          {showCommentBox ? 'Hide comment' : 'Add comment'}
        </button>
      </div>

      {showCommentBox && (
        <form onSubmit={handleCommentSubmit} className="w-full space-y-2">
          <textarea
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            rows={2}
            className="w-full rounded-lg border border-[#5f4635] bg-[#1e1815] px-2 py-2 text-xs text-[#f4e5d6]"
            placeholder="Share a detail about what was helpful or confusing"
          />
          <button type="submit" className="rounded-lg bg-[#7d5a42] px-2 py-1 text-xs text-[#f8ebdf]">
            Send feedback
          </button>
        </form>
      )}

      {submitted && <span className="text-[11px] text-[#7dbb8d]">Thanks — noted!</span>}
    </div>
  );
};

export default FeedbackWidget;
