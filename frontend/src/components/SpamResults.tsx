import { useState } from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  TrashIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  DocumentArrowDownIcon,
  ChatBubbleLeftIcon
} from '@heroicons/react/24/outline';
import { SpamDetectionResponse, SpamComment, getRiskLevelColor, getSpamTypeColor, getConfidenceColor } from '@/lib/api';
import { formatRelativeTime, downloadAsJson, downloadAsCsv } from '@/lib/utils';

interface SpamResultsProps {
  data: SpamDetectionResponse;
  isDryRun: boolean;
}

export function SpamResults({ data, isDryRun }: SpamResultsProps) {
  const [expandedComments, setExpandedComments] = useState<Set<string>>(new Set());
  const [filterType, setFilterType] = useState<'all' | 'spam' | 'clean'>('all');
  const [sortBy, setSortBy] = useState<'confidence' | 'date' | 'risk'>('confidence');

  if (!data.success) {
    return (
      <div className="card border-red-200 bg-red-50">
        <div className="card-body">
          <div className="flex items-center space-x-2 text-red-700">
            <XCircleIcon className="h-5 w-5" />
            <span className="font-medium">Processing Failed</span>
          </div>
          <p className="text-red-600 mt-2">{data.errors?.[0] || 'Unknown error occurred'}</p>
        </div>
      </div>
    );
  }

  const spamComments = data.spam_comments || [];
  const cleanComments = data.spam_comments?.filter((c: SpamComment) => !c.analysis.is_spam) || [];

  const toggleComment = (commentId: string) => {
    const newExpanded = new Set(expandedComments);
    if (newExpanded.has(commentId)) {
      newExpanded.delete(commentId);
    } else {
      newExpanded.add(commentId);
    }
    setExpandedComments(newExpanded);
  };

  const filteredComments = spamComments.filter((comment: SpamComment) => {
    // When not in dry run mode (remove spam clicked), show only moderated rejected messages
    if (!isDryRun) {
      return comment.analysis.is_spam && comment.analysis.recommended_action === 'delete';
    }
    
    // In dry run mode, use normal filtering
    if (filterType === 'spam') return comment.analysis.is_spam;
    if (filterType === 'clean') return !comment.analysis.is_spam;
    return true;
  });

  const sortedComments = [...filteredComments].sort((a, b) => {
    switch (sortBy) {
      case 'confidence':
        return (b.analysis.confidence || 0) - (a.analysis.confidence || 0);
      case 'date':
        return new Date(b.published_at).getTime() - new Date(a.published_at).getTime();
      case 'risk':
        const riskOrder = { high: 3, medium: 2, low: 1 };
        return (riskOrder[b.analysis.risk_level as keyof typeof riskOrder] || 0) - 
               (riskOrder[a.analysis.risk_level as keyof typeof riskOrder] || 0);
      default:
        return 0;
    }
  });

  const exportData = () => {
    const exportComments = spamComments.map((comment: SpamComment) => ({
      id: comment.id,
      author: comment.author,
      text: comment.text,
      is_spam: comment.analysis.is_spam,
      confidence: comment.analysis.confidence,
      risk_level: comment.analysis.risk_level,
      spam_type: comment.analysis.spam_type,
      published_at: comment.published_at,
      like_count: comment.like_count,
    }));

    return {
      summary: data.summary,
      comments: exportComments,
      exported_at: new Date().toISOString(),
    };
  };

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            {isDryRun ? (
              <EyeIcon className="h-5 w-5 mr-2 text-blue-600" />
            ) : (
              <CheckCircleIcon className="h-5 w-5 mr-2 text-green-600" />
            )}
            {isDryRun ? 'Analysis Results (Dry Run)' : 'Processing Complete'}
          </h3>
        </div>
        <div className="card-body">
          {isDryRun && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center space-x-2 text-blue-700">
                <ExclamationTriangleIcon className="h-4 w-4" />
                <span className="text-sm font-medium">Dry Run Mode</span>
              </div>
              <p className="text-blue-600 text-sm mt-1">
                No comments were actually deleted. This is a preview of what would happen.
              </p>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {data.processing_stats.total_comments}
              </div>
              <div className="text-sm text-gray-600">Total Comments</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {data.processing_stats.spam_detected}
              </div>
              <div className="text-sm text-gray-600">Spam Detected</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {data.processing_stats.high_confidence_spam || 0}
              </div>
              <div className="text-sm text-gray-600">High Confidence Gambling</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {data.processing_stats.total_comments - data.processing_stats.spam_detected}
              </div>
              <div className="text-sm text-gray-600">Clean Comments</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {isDryRun ? (data.processing_stats.high_confidence_spam || 0) : (data.processing_stats.deleted_count || 0)}
              </div>
              <div className="text-sm text-gray-600">
                {isDryRun ? 'Would Delete' : 'Deleted'}
              </div>
            </div>
          </div>

          {data.summary.processing_time && (
            <div className="mt-4 text-sm text-gray-600">
              Processing completed in {data.summary.processing_time}
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="card-body">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center space-x-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mr-2">Filter:</label>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value as any)}
                  className="input-field text-sm"
                  disabled={!isDryRun}
                >
                  {!isDryRun ? (
                    <option value="spam">Moderated Rejected ({filteredComments.length})</option>
                  ) : (
                    <>
                      <option value="all">All Comments ({spamComments.length})</option>
                      <option value="spam">Spam Only ({spamComments.filter((c: SpamComment) => c.analysis.is_spam).length})</option>
                      <option value="clean">Clean Only ({cleanComments.length})</option>
                    </>
                  )}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mr-2">Sort by:</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="input-field text-sm"
                >
                  <option value="confidence">Confidence</option>
                  <option value="date">Date</option>
                  <option value="risk">Risk Level</option>
                </select>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => downloadAsJson(exportData(), `spam-analysis-${Date.now()}`)}
                className="btn-secondary text-sm"
              >
                <DocumentArrowDownIcon className="h-4 w-4 mr-1" />
                Export JSON
              </button>
              <button
                onClick={() => downloadAsCsv(spamComments, `spam-analysis-${Date.now()}`)}
                className="btn-secondary text-sm"
              >
                <DocumentArrowDownIcon className="h-4 w-4 mr-1" />
                Export CSV
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Comments List */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900">
            {!isDryRun ? 'Moderated Rejected Comments' : 'Comments'} ({filteredComments.length})
          </h3>
        </div>
        <div className="card-body p-0">
          {filteredComments.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <ChatBubbleLeftIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>No comments found with the current filter.</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {filteredComments.map((comment: SpamComment) => (
                <CommentItem
                  key={comment.id}
                  comment={comment}
                  isExpanded={expandedComments.has(comment.id)}
                  onToggle={() => toggleComment(comment.id)}
                  isDryRun={isDryRun}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface CommentItemProps {
  comment: SpamComment;
  isExpanded: boolean;
  onToggle: () => void;
  isDryRun: boolean;
}

function CommentItem({ comment, isExpanded, onToggle, isDryRun }: CommentItemProps) {
  const isLongComment = comment.text.length > 200;
  const displayText = isExpanded || !isLongComment 
    ? comment.text 
    : comment.text.slice(0, 200) + '...';

  return (
    <div className={`p-4 ${comment.analysis.is_spam ? 'bg-red-50' : 'bg-white'}`}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            comment.analysis.is_spam ? 'bg-red-100' : 'bg-green-100'
          }`}>
            {comment.analysis.is_spam ? (
              <XCircleIcon className="h-4 w-4 text-red-600" />
            ) : (
              <CheckCircleIcon className="h-4 w-4 text-green-600" />
            )}
          </div>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <span className="font-medium text-gray-900">
                {comment.author}
              </span>
              <span className="text-sm text-gray-500">
                {formatRelativeTime(comment.published_at)}
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              {comment.analysis.is_spam && (
                <>
                  <span className={`badge ${getRiskLevelColor(comment.analysis.risk_level)}`}>
                    {comment.analysis.risk_level} risk
                  </span>
                  {comment.analysis.spam_type && (
                    <span className={`badge ${getSpamTypeColor(comment.analysis.spam_type)}`}>
                      {comment.analysis.spam_type}
                    </span>
                  )}
                  {comment.analysis.confidence && (
                    <span className={`badge ${getConfidenceColor(comment.analysis.confidence)}`}>
                      {Math.round(comment.analysis.confidence * 100)}% confident
                    </span>
                  )}
                </>  
              )}
              {isDryRun && comment.analysis.is_spam && (
                <span className="badge bg-blue-100 text-blue-800">
                  <TrashIcon className="h-3 w-3 mr-1" />
                  Would delete
                </span>
              )}
            </div>
          </div>
          
          <div className="text-gray-900 whitespace-pre-wrap">
            {displayText}
          </div>
          
          {isLongComment && (
            <button
              onClick={onToggle}
              className="mt-2 text-sm text-primary-600 hover:text-primary-700 flex items-center"
            >
              {isExpanded ? (
                <>
                  <ChevronUpIcon className="h-4 w-4 mr-1" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDownIcon className="h-4 w-4 mr-1" />
                  Show more
                </>
              )}
            </button>
          )}
          
          <div className="flex items-center space-x-4 mt-3 text-sm text-gray-500">
            <span>{comment.like_count} likes</span>
            <a
              href={`https://www.youtube.com/watch?lc=${comment.id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:text-primary-700"
            >
              View on YouTube
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}