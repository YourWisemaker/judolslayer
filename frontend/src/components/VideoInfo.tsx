import { PlayIcon, EyeIcon, HandThumbUpIcon, ChatBubbleLeftIcon } from '@heroicons/react/24/outline';
import { LoadingSpinner } from './LoadingSpinner';
import { formatRelativeTime } from '@/lib/utils';
import { VideoInfoResponse, formatNumber } from '@/lib/api';

interface VideoInfoProps {
  videoId: string;
  isLoading: boolean;
  data?: VideoInfoResponse;
}

export function VideoInfo({ videoId, isLoading, data }: VideoInfoProps) {
  if (isLoading) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <PlayIcon className="h-5 w-5 mr-2 text-primary-600" />
            Video Information
          </h3>
        </div>
        <div className="card-body">
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        </div>
      </div>
    );
  }

  if (!data?.success || !data.video_info) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <PlayIcon className="h-5 w-5 mr-2 text-primary-600" />
            Video Information
          </h3>
        </div>
        <div className="card-body">
          <div className="text-center py-8 text-gray-500">
            <PlayIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>Enter a valid video ID and API key to see video information</p>
          </div>
        </div>
      </div>
    );
  }

  const { video_info } = data;

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <PlayIcon className="h-5 w-5 mr-2 text-primary-600" />
          Video Information
        </h3>
      </div>
      <div className="card-body space-y-4">
        {/* Thumbnail */}
        <div className="aspect-video w-full rounded-lg overflow-hidden bg-gray-100">
          <img
            src={video_info.thumbnail_url}
            alt={video_info.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.src = `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
            }}
          />
        </div>

        {/* Title */}
        <div>
          <h4 className="font-semibold text-gray-900 line-clamp-2 leading-tight">
            {video_info.title}
          </h4>
          <p className="text-sm text-gray-600 mt-1">
            by {video_info.channel_title}
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <EyeIcon className="h-4 w-4" />
            <span>{formatNumber(video_info.view_count)} views</span>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <HandThumbUpIcon className="h-4 w-4" />
            <span>{formatNumber(video_info.like_count)} likes</span>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <ChatBubbleLeftIcon className="h-4 w-4" />
            <span>{formatNumber(video_info.comment_count)} comments</span>
          </div>
          <div className="text-sm text-gray-600">
            <span>{formatRelativeTime(video_info.published_at)}</span>
          </div>
        </div>

        {/* Description Preview */}
        {video_info.description && (
          <div>
            <h5 className="text-sm font-medium text-gray-900 mb-2">Description</h5>
            <p className="text-sm text-gray-600 line-clamp-3">
              {video_info.description}
            </p>
          </div>
        )}

        {/* Video Link */}
        <div className="pt-2 border-t border-gray-200">
          <a
            href={`https://youtu.be/${videoId}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            <PlayIcon className="h-4 w-4 mr-1" />
            Watch on YouTube
          </a>
        </div>
      </div>
    </div>
  );
}