import { useQuery } from '@tanstack/react-query';
import { spamDetectionAPI, VideoInfoResponse } from '@/lib/api';
import { validateVideoId, validateApiKey } from '@/lib/api';

export const useVideoInfo = (videoId?: string) => {
  return useQuery<VideoInfoResponse, Error>({
    queryKey: ['videoInfo', videoId],
    queryFn: () => {
      if (!videoId) {
        throw new Error('Video ID is required');
      }
      return spamDetectionAPI.getVideoInfo({
        video_id: videoId,
      });
    },
    enabled: Boolean(
      videoId && 
      validateVideoId(videoId)
    ),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error: any) => {
      // Don't retry on 4xx errors
      if (error?.response?.status >= 400 && error?.response?.status < 500) {
        return false;
      }
      return failureCount < 2;
    },
  });
};